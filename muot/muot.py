#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import sys
#import json
import os
from datetime import datetime
import csv
import re

import tweepy

from auxfnct import *

#Redefine the class to process each tweet read according to the filter

class muotStreamListener(tweepy.StreamListener):

	lstUsers=None
	lstTweetCSV=None
	useES=False
	es=None
	indexName=None
	n=0

	def __init__(self, **kwargs):
		
		"""The init of the class, ready to receive different args"""
		#Extend the constructor
		if "users" in kwargs:
			self.lstUsers=kwargs['users']
		if "tweetCSV" in kwargs:
			self.lstTweetCSV=kwargs['tweetCSV']
		self.useES = kwargs['useES']
		if self.useES:
			self.es=kwargs['esInstance']
			self.indexName=kwargs['indexName']	
		
		#Call the super constructor
		super(muotStreamListener, self).__init__()
	
	def on_connect(self):
		
		"""If the connection is satisfactory"""
		
		print timeStr() + "Connected to the Twitter Stream"
		print "Press CTRL+C to finish the tracking"
		
	def on_status(self, status):
		
		"""Method called every time a Tweet is catched"""
		
		self.n += 1
		print "\r"+str(self.n)+ " tweets read",

		try:
			#Get only no retweeted Tweets
			if not status.retweeted:
				user_name = status.author.screen_name.encode('utf-8')
				json_data = status._json
				place=""
				if status.place:
					if status.place.full_name:
						place = status.place.full_name.encode('utf-8')
			
					
				#Index in Elasticsearch in case it is enabled
				if self.useES:
					#Create new field for coordinates parsing to ElasticSearch in string mode
					if json_data['coordinates']:
						json_data['coordinates']['coord_string']=(str(json_data['coordinates']['coordinates'][1]) + ","+str(json_data['coordinates']['coordinates'][0])).encode('utf-8')
					self.es.index(index=self.indexName, doc_type="twitter_type", body=json_data)

				#Write the tweet to the tweets csv file
				#First, delete new line character from Twitter text
				text_formated = re.sub(r"\n", " ", status.text.encode('utf-8'))
				
				#Create the row
				tweetRow = [status.created_at, 
							user_name.encode('utf-8'), 
							status.author.name.encode('utf-8'), 
							text_formated, 
							status.author.followers_count, 
							status.author.friends_count, 
							status.coordinates, 
							place, 
							status.lang.encode('utf-8'), 
							status.source.encode('utf-8')]
							
				#Put the row in the file
				with open(self.lstTweetCSV, 'ab') as twitterFile:
					twitterCSVwriter = csv.writer(twitterFile)
					twitterCSVwriter.writerow(tweetRow)
				twitterFile.close()
				
				#Check if the user has been found before
				if user_name not in self.lstUsers:
					self.lstUsers.append(user_name)
		

		except Exception, e:
			print (e)

	def on_error(self, status_code):
		""" Method to control any error during the listening on Twitter"""
		
		#Catch the error related to the rate limit of connections
		if status_code == 420:
			print timeStr()+ "Error connecting to Twitter stream API, wait some time until try connecting again"
			raw_input("Press Enter to continue")
			return False

			


def monitorStream():
	
	"""Get key words from stdin and monitor the Twitter stream. Option 1"""
	
	#Read the terms
	while True:
		
		os.system('clear')
		print "The maximun length for each term is 60 characters and the limit of terms is 400\n"
		key_words=raw_input("Enter the key words or phrases and press Enter (separated by commas): ")
		terms = [each.strip() for each in key_words.split(',')]
		
		if len(terms) > 400:
			raw_input (timeStr() + "The limit of terms is 400\nPress any key and try again")


		else:
			for each in terms:
				if len(each) > 60:
					raw_input (timeStr()+"The maximun length for each term is 60 characters\nPress any key and try again")
					break
			break
	

	
	#Create the Oauth object
	auth= twitterOauthHandler()
	
	
	#Create the CSV file for the tweets
	tweetCSVheader =['created_at', 
					'screen_name', 
					'name', 'text', 
					'followers_count', 
					'friends_count', 
					'coordinates', 
					'place', 
					'lang', 
					'source']
					
	fileName="Tweets_stream_" + datetime.now().strftime("%d-%m-%Y %H:%M")
	tweetCSV = createTwitterCSV(fileName, tweetCSVheader)
	
	#variables for the streamer object
	users=[]
	
	#Define the use of ElasticSearch and create the listener
	useES = useElasticsearch()
	
	if useES:
		#create the ElasticSearch index
		indexName = "stream_tweets_" + datetime.now().strftime("%d-%m-%Y_%H:%M")
		esInstance = createIndexES(indexName)
		listener = muotStreamListener(users=users, tweetCSV=tweetCSV, useES=useES, esInstance=esInstance, indexName=indexName)
	
	else:
		listener = muotStreamListener(users=users, tweetCSV=tweetCSV, useES=useES)
	
	
	#Create the Twitter streamer API consumer object
	try:
		streamer = tweepy.Stream(auth=auth, listener=listener)
		print timeStr() + "streamer created"
	except Exception, e:
		print (e)
		raw_input (timeStr() + "Error creating the stream object. Press any key to continue")
		return False
		

	#Start the active Listening on Twitter	
	print (timeStr() + "Listening for: " + ', '.join(terms))	
	try:
		streamer.filter(None,terms)
	
	#Manage the finish of listening	triggered by Ctrl+C
	except KeyboardInterrupt:
		streamer.disconnect()
		os.system('clear')
		print "\n" + timeStr() + "Stream of tweets finished. " + str(len(users)) + " users catched"
		
		while True:
			processUser = raw_input(timeStr()+"Search for profiles and mails of each user?[y,n] ").lower()
			if processUser == 'y':
				#Proccess each user looking for profiles and mails in other platforms
				for eachUser in users:
					lookForUsu(eachUser)
					lookForMail(eachUser)
				os.system('clear')
				break
			if processUser == 'n':
				break
		print timeStr()+"The tweets are in: " + tweetCSV
		raw_input("Press Enter to finish")
		sys.exit(0)


def userTrack():
	
	"""Monitoring an user on the Twitter Stream"""
	
	os.system('clear')
	userName = (str(raw_input("Enter the user name or the userID and press Enter: ")))
	print timeStr() + "Tracking: " + userName
	
	
	#Create the Oauth object
	auth= twitterOauthHandler()
	
	#Check if the user is in Twitter through the error response code 50
	twitterAPI = tweepy.API(auth_handler=auth)

	try:
		userID = (twitterAPI.get_user(str(userName))).id_str
		
	except tweepy.TweepError, e:
		if e.message[0]['code'] == 50:
			print timeStr() + "The user " + str(userName) + " has not been found on Twitter"
			raw_input("Press Enter to go back to the menu")
		return False
		
	#Control the Twitter rate limit
	except tweepy.RateLimitError:
		print timeStr() + "Twitter rate limit exceded, wait at least 15 minutes before try again"
	
	#Create the CSV file for the tweets
	tweetCSVheader =['created_at', 
					'screen_name', 
					'name', 'text', 
					'followers_count', 
					'friends_count', 
					'coordinates', 
					'place', 
					'lang', 
					'source']
					
	fileName=userName+"_tweets"+datetime.now().strftime("[%d-%m-%Y_%H:%M]")
	tweetCSV = createTwitterCSV(fileName, tweetCSVheader)	
	
	
	#Define the use of ElasticSearch and create the listener
	useES = useElasticsearch()
	if useES:
		#create the ElasticSearch index
		indexName = "tweets_" + userName
		esInstance = createIndexES(indexName)
		listener = muotStreamListener(users=[userID], tweetCSV=tweetCSV, useES=useES, esInstance=esInstance, indexName=indexName)
	else:
		listener = muotStreamListener(users=[userID],tweetCSV=tweetCSV, useES=useES)
		
	
	#Create the Twitter streamer API consumer object
	try:
		streamer = tweepy.Stream(auth=auth, listener=listener)
		print timeStr() + "streamer created"
	except Exception, e:
		print (e)
		

	#Start active listening
	try:
		streamer.filter(follow=[userID])
	except KeyboardInterrupt:
		streamer.disconnect()
		os.system('clear')

		while True:
			processUser = raw_input("\nDo you want to look for profiles and mails of " + userName + "?[y,n]").lower()
			if processUser == 'y':
				#Proccess each user look for profiles and mails in other platforms
				lookForUsu(userName)
				lookForMail(userName)
				os.system('clear')
				break
			if processUser == 'n':
				break
		print timeStr()+"The tweets are in: " + tweetCSV
		raw_input("Press Enter to finish")
		sys.exit(0)
	

def catchUserTweets():
	
	""" Reads last n tweets of the user timeline """
	
	os.system('clear')
	
	#Get the user and the number of tweets required (check if they are in the limits
	userName = (str(raw_input("Enter the user name or the userID and press Enter ")))
	while True:
		try:
			nTweets = int(raw_input("Enter the number of tweets to retrieve (max 3200)"))
			if nTweets not in range(1,3201):
				raise ValueError
			else:
				break
		except ValueError:
			print "Number not valid. Type a value from 1 to 3200"
	print timeStr() + "The user is: " + userName
	
	
	#Create the Oauth object
	auth= twitterOauthHandler()
	
	#Check if the user is in Twitter
	twitterAPI = tweepy.API(auth_handler=auth)

	try:
		userID = (twitterAPI.get_user(str(userName))).id_str
		
	except tweepy.TweepError, e:
		if e.message[0]['code'] == 50:
			print timeStr() + "The user " + str(userName) + " has not been found on Twitter"
			raw_input("Press Enter to go back to the menu")
		return False
		
	except tweepy.RateLimitError:
		print timeStr() + "Rate limit exceded, wait at least 15 minutes before try again"

	
	#Create the csv file for the tweets
	tweetCSVheader =['created_at', 
					'screen_name', 
					'name', 'text', 
					'followers_count', 
					'friends_count', 
					'coordinates', 
					'place', 
					'lang', 
					'source']
					
	fileName=userName+"_tweets"+datetime.now().strftime("[%d-%m-%Y_%H:%M]")
	tweetCSV = createTwitterCSV(fileName, tweetCSVheader)

	#Retrieve tweets in blocks of 200 max
	if nTweets <= 200:
		listOfTweets = getUserTweets(twitterAPI, userID, nTweets)

	else:
		listOfTweets = []
		ntBlock = nTweets // 200
		maxTweetID=None
		moreTweets = True
		while ntBlock > 0:
			
			#The max ID for the next block is the [last tweet ID -1] of the current block
			tempTweets = getUserTweets(twitterAPI, userID, 200, maxTweetID)
			if len(tempTweets) == 0:
				moreTweets = False
				break
			maxTweetID=(tempTweets[-1].id)-1
			listOfTweets=listOfTweets + tempTweets
			ntBlock = ntBlock - 1
		 		
		restTweets = nTweets % 200
		if restTweets > 0 and moreTweets:
			maxTweetID=(listOfTweets[-1].id)-1
			listOfTweets = listOfTweets + (getUserTweets(twitterAPI, userID, restTweets, maxTweetID))

	print timeStr() + str(len(listOfTweets)) + " tweets gathered"
		
	#Write each tweet to the tweets csv file
	for tweet in listOfTweets:
		
		#Delete \n from the tweet text
		text_formated = re.sub(r"\n", " ", tweet.text.encode('utf-8'))
			
		#Create the row
		tweetRow = [tweet.created_at,
					tweet.author.screen_name,
					tweet.author.name.encode('utf-8'), 
					text_formated, 
					tweet.author.followers_count, 
					tweet.author.friends_count, 
					tweet.coordinates, 
					tweet.lang.encode('utf-8'), 
					tweet.source.encode('utf-8')]
						
		#Write the tweet to the file
		with open(tweetCSV, 'ab') as twitterFile:
			twitterCSVwriter = csv.writer(twitterFile)
			twitterCSVwriter.writerow(tweetRow)
		twitterFile.close()
	
	while True:
		processUser = raw_input("\nDo you want to look for profiles and mails of " + userName + "?[y,n]").lower()
		
		if processUser == 'y':
			
			#Proccess each user look for profiles and mails in other platforms
			lookForUsu(userName)
			lookForMail(userName)
			os.system('clear')
			break
		
		if processUser == 'n':
			break
			
	print timeStr()+"The tweets are in: " + tweetCSV
	raw_input ("Press Enter to finish")
	sys.exit(0)
	

def main():
	
	""" Main function, run when program is executed"""
	
	#Menu and input options
	while True:
		optionsMenu()
		menuOption = str(raw_input("\n\tSelect an option and press Enter "))

		if menuOption == '1':
			monitorStream()
			
		elif menuOption == '2':
			userTrack()
		
		elif menuOption == '3':
			catchUserTweets()
		
		elif menuOption.lower() == 'h':
			showHelp()
			continue
		elif menuOption.lower() == 'q':
			sys.exit(0)

		else:
			os.system('clear')
			print "\n\nChoose an option [1,2,3] use 'h' for help or 'q' to finish"
			raw_input("Press Enter to continue")
		



if __name__ == "__main__":
	main()
