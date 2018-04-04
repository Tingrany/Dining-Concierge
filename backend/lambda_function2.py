from __future__ import print_function

import argparse
import json
import pprint
from botocore.vendored import requests
import sys
import urllib
import boto3
from datetime import date
from time import mktime
import time
from urllib.parse import quote_plus
import datetime


# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode


# Yelp Fusion no longer uses OAuth as of December 7, 2017.
# You no longer need to provide Client ID to fetch Data
# It now uses private keys to authenticate requests (API Key)
# You can find it on
# https://www.yelp.com/developers/v3/manage_app
API_KEY= "QO1mvO3lzL14Zt6jpGF0OT8D87MB8is2iKS69acuAqcLC7anwazh97SpIP6I0ieE3PBPubaH0AvqjNppRS3hgGFmJIG9_dNazvbv1uhU52T93IsQZyAPFhMgIKq-WnYx" 


# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.



def request(host, path, api_key, url_params=None):
    """Given your API_KEY, send a GET request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        dict: The JSON response from the request.

    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }

    print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()


def search(api_key, term, location, unixTime, price):
    """Query the Search API by a search term and location.

    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.

    Returns:
        dict: The JSON response from the request.
    """

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'open_at': int(unixTime),
        'price': price,
        'limit': 3   #SEARCH_LIMIT
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)


def get_business(api_key, business_id):
    """Query the Business API by a business ID.

    Args:
        business_id (str): The ID of the business to query.

    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path, api_key)


def query_api(event, unixTime):
    """Queries the API by the input values from the user.

    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """

    term = event['RestaurantType']
    location = event['Location']

    response = search(API_KEY, term, location, unixTime, event['Price'])

    businesses = response.get('businesses')

    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return
    print(businesses)
    output = "Hello! Here are my {0} restaurant suggestions for {1} people, for {2} at {3}: ".format(event['RestaurantType'], event['PeopleNum'], event['DiningDate'], event['DiningTime'])
    for i in range(len(businesses)):
        #business_id = businesses[0]['id']
        business_name = businesses[i]['name']
        business_address = businesses[i]['location']['display_address']
        alias = businesses[i]['categories'][0]['alias'].title()
        expectPrice = businesses[i]['price']
        rate = businesses[i]['rating']
        print(u'Result for business "{0}" found,'.format(business_name)+u'address is "{0}"'.format(business_address))
        output = output + "{0} Restaurant {1}: {2}, rating: {3}, price as {4}, located at {5}. ".format(alias, i+1, business_name, rate, expectPrice, str(business_address).split(",")[0].strip("['']") + "," + str(business_address).split(",")[1].replace("'", "")+","+str(business_address).split(",")[2].replace("']", ""))   
    print(output)
    return output
    # print(u'{0} businesses found, querying business info ' \
    #     'for the top result "{1}" ...'.format(
    #         len(businesses), business_id))
    #response = get_business(API_KEY, business_id)

    
    #pprint.pprint(response, indent=2)
    
def sqsMessage():
    sqs = boto3.client('sqs')  #create SQS client
    queue_url = 'https://sqs.us-east-1.amazonaws.com/153684740928/DiningSuggestion'
    #queue_url = 'https://sqs.us-east-1.amazonaws.com/660585719256/test'

    #use url to receive message from SQS queue
    response_sqs = sqs.receive_message(
        QueueUrl = queue_url,
        AttributeNames= ['SentTimestamp'],
        MaxNumberOfMessages = 1,
        MessageAttributeNames=['All'],
        VisibilityTimeout = 0,
        WaitTimeSeconds = 20
        )
    event1 = response_sqs['Messages'][0]['Body']
    receipt_handle = response_sqs['Messages'][0]['ReceiptHandle']
    response_sqs = sqs.delete_message(
        QueueUrl = 'https://sqs.us-east-1.amazonaws.com/153684740928/DiningSuggestion',
        ReceiptHandle = receipt_handle
        )
    print(event1)
    return event1
    #RestaurantType = response_sqs['Messages'][0]['Body']['RestaurantType']
    #Location = response_sqs['Messages'][0]['Body']['Location']
    #

    
def getLocalUnix(event):
    #calculate the dining time in local Unix format
    time = event['DiningDate'].split("-")
    start = date(int(time[0]), int(time[1]), int(time[2]))
    dayTime = mktime(start.timetuple())  #loss 4 hours, 14400 seconds should be added
    hm = event['DiningTime'].split(":")
    local_unixTime = round(int(dayTime) + int(hm[0])*3600 + int(hm[1])*60 + 14400) #This is local Unix time
    #local_unixTime = 1522595640
    print(local_unixTime)
    return local_unixTime
    
def send_to_sns(message, event):
    sns = boto3.client('sns')
    sns.publish(
        #TopicArn=message['topic'],
        #Subject=message['subject'],
        Message=message,
        PhoneNumber = event['PhoneNum']
    )

    return ('Sent a message to an Amazon SNS topic.')
    

def lambda_handler(event, context):

    try:
        event = json.loads(sqsMessage())
        event['DiningDate'] = "2018-04-03"
        #query_api(event, getLocalUnix(event))
        send_to_sns(query_api(event, getLocalUnix(event)), event)
        
    except HTTPError as error:
        sys.exit(
            'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                error.code,
                error.url,
                error.read(),
            )
        )




        