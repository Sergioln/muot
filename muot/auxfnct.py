# -*- coding: utf-8 -*-

""" Auxiliary functions for the muot application"""

import os
import sys
import time
from datetime import datetime
import ConfigParser
import csv
import urllib2
import textwrap

import osrframework.usufy as usufy
import osrframework.mailfy as mailfy


import tweepy
from elasticsearch import Elasticsearch

def optionsMenu():
	
	"""Prints the menu of options"""
	
        os.system('clear')
        print ("""


	  _ __ ___  _   _  ___ | |_ 
	 | '_ ` _ \| | | |/ _ \| __|
	 | | | | | | |_| | (_) | |_ 
	 |_| |_| |_|\__,_|\___/ \__|
								
								
                                                                   
	Monitoring Users On Twitter. Track the content of the tweets
	looking up for a key word or phrase, try to find profiles 
	with his alias in other platforms, then try to find a public
	emails registered with that alias 
	""")
        print ("\t[1] Track the Twitter stream filtering by a key word")
        print ("\t[2] Track an user in the Twitter stream")
        print ("\t[3] Track an user timeline (max 3200 tweets)")
        print ("\t[h] Show the help")
        print ("\t[q] Close the application")


def lookForUsu (alias):
	
	"""Launches the usufy application to find profiles in many platforms"""
	
	#Create the list with the parameters
	usufyArgs=["-n"] + [str(alias)] + ["-o"] + ["./profiles"] + ["-F"] + [str(alias)+"_profiles"]
	parser = usufy.getParser()
	args = parser.parse_args(usufyArgs)
	try:
		usufy.main(args)
	except Exception as e:
		print "Error proccessing the profiles of the user: " + str(alias)


def lookForMail (alias):
	
	"""Launches the mailfy application to find email adrresses related to the alias"""
	
	#Create the list with the parameters
	mailfyArgs=["-n"] + [str(alias)] + ["-o"] + ["./profiles"] + ["-F"] + [str(alias)+"_mails"]
	parser = mailfy.getParser()
	args = parser.parse_args(mailfyArgs)
	try:
		mailfy.main(args)
	except Exception as e:
		print "Error proccessing the mails of the user: " + str(alias)



	
def createTwitterCSV(fileName, header, pathFile="./profiles/"):
	
	"""Create csv file  with the header provided to store the tweets"""
	
	#Create the directory in case it does not exits
	if not os.path.isdir(pathFile):
		os.makedirs(pathFile)
		
	tweetCSV = pathFile+fileName+".csv"
	with open(tweetCSV, 'wb') as twitterFile:
		twitterCSVwriter = csv.writer(twitterFile)
		twitterCSVwriter.writerow(header)
	twitterFile.close()
	return tweetCSV


def timeStr():
	
	"""Returns a timestamp predefined string to use in logs"""
	
	#return datetime.now().strftime("[%d/%m/%y %H:%M:%S]")
	return datetime.now().strftime("[%H:%M:%S]")



def useElasticsearch():
	
	""" Enable the use of ElasticSearch, returns true if module can be activated """
	
	aES = str((raw_input("Index Tweets on Elasticsearch (deafault=n)?[y/n]"))).lower()
	useES = False
	
	if aES == 'y':
		try:
			#Check if ES is running in the localhost
			urllib2.urlopen('http://localhost:9300')
			useES = True
			print timeStr() + "ES node found. Indexing Tweets in ElasticSearch"
		except urllib2.URLError, e:
			print timeStr()+"Elasticsearch node not found, ES module disabled"
		
	else:
		print timeStr() + "Elasticsearch indexing disabled"
	return useES



def createIndexES(indexName):
	
	"""Function to create the index in Elasticsearch according to the template defined"""
	
	#ElasticSearch connector
	es = Elasticsearch()

	#Template for the tweets parsing (geo_point)
	twitter_mapping = {
		"mappings": {
			"tweets_*": {
				"properties": {
					"coordinates": {
						"properties": {
							"coord_string": {
								"type": "geo_point"
							},
							"type": {
								"type": "string"
							}
						}
					}
				}
			}
		}
	}
	
	#Delete the index with the same name if any
	if es.indices.exists(index=str(indexName)):
		es.indices.delete(index=str(indexName))
	
	#Create the index
	try:
		es.indices.create(index=str(indexName), ignore=400, update_all_types=True, body=twitter_mapping)
		print timeStr() + "Index: " + str(indexName) + " successfully created" 
	except Exception, e:
		print (e)
	
	return es


def getUserTweets(api, userid, countTweets, maxID=None):
	
	"""Return n tweets of the user time line"""
	
	try:
		lstOfTweets= (api.user_timeline(user_id=userid, count=countTweets, max_id=maxID))
	except tweepy.RateLimitError:
		print timeStr()+"Twitter rate limit exceded, waiting 15 minutes until next query"
		time.sleep(900)
		
	return lstOfTweets


def twitterOauthHandler():
	
	"""This function creates the handler for the Oauth autentication 
	on Twitter with the credentials provided in the configuration file"""
        
	#Get Twitter credentials from twitter-API.conf file
	try:
		confReader = ConfigParser.ConfigParser()
		confReader.read("./configuration/twitter-API-access.conf")
		consumer_key = confReader.get("CONSUMER", 'key')
		consumer_secret = confReader.get("CONSUMER", 'secret')
		access_token = confReader.get("ACCESS", 'token')
		access_token_secret  = confReader.get("ACCESS", 'secret')
	except ConfigParser.Error:
		print timeStr() + "Error accessing to the Twitter API configuration file, see README file for more information"
		sys.exit(0)
		
	#Create the Oauth handler and check if the credentials are valid
	try:
		auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
		print timeStr() + "OauthHandler created"
		auth.set_access_token(access_token, access_token_secret)
		try:
			apiTest = tweepy.API(auth)
			apiTest.me()
		except Exception, e:
				print timeStr() + "Error with the credentials, check twtter-API-access.conf file"
				sys.exit(0)
		return auth
	except Exception, e:
		print (e)

def showHelp():
	os.system('clear')
	allText="""This application connects to Twitter and allows to monitor the stream or an user. The tweets are stored in a CSV file.\
After the monitorization, you are allowed to find profiles in many OSNs and mail services using OSRFramework by i3visio.\n
Option 1. Monitoring the Twitter real time Stream. Choose keywords and filter the Twitter Stream by them.
Option 2. Monitoring an user's activity on Twitter.
Option 3. Get the last n tweets (3200 max.) of an user.\n"""
	print allText
	raw_input("Press Enter to continue")
