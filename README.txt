##########################################
############## Dependencies ##############
##########################################

This application has been developed to work in Linux 32 bit system and it runs in Python 2.7, although it could work in Python 3.x environment (not tested).

The following Python packages must been installed before launch the application:

-osrframework
-tweepy
-elasticsearch

The easiest way to install all of them is using the pip (PyPI) manager with the requirements file:

pip install -r requirements.txt


###########################################
########## Optional dependencies ##########
###########################################

If you want to use Elasticsearch indexer and Kibana they must be executed as a local server on the predefined port 9200. The versions that have been tested are:

-Elasticsearch 2.4.3
-Kibana 4.6.3 (x86)

They can be downloaded from the original source:

wget https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.4.3/elasticsearch-2.4.3.tar.gz

wget https://download.elastic.co/kibana/kibana/kibana-4.6.3-linux-x86.tar.gz


###########################################
################## Usage ##################
###########################################

Before launch the application, you must fill the twitter-API-access.conf file with your own tokens ank keys for the Twiiter application (see apps.twitter.com for more information). 

Then, just run "./muot.py" or "python ./muot.py".

NOTE: In case you cannot find the configuration file, just create it in "./configuration/twitter-API-access.conf" with the following content:

[CONSUMER]

key: <Put your own consumer key>
secret: <Put your own consumer secret>



[ACCESS]
token: <Put the token of your app>
secret: <Put the secret of your app>
