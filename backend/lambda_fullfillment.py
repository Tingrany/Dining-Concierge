"""
"""
import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']
    

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response


""" --- Send message to SQS --- """


def send_SQS(intent_request, SQS):
    message = get_slots(intent_request)
    #logger.debug('In the sender.')
    # Get the service resource
    sqs = boto3.resource('sqs')

    # Get the queue
    queue = sqs.get_queue_by_name(QueueName = SQS)

    # Create a new message
    queue.send_message(MessageBody = json.dumps(message))
    

""" --- Functions that control the bot's behavior --- """

def send_sqs_message(intent_request):
    """
    Performs dialog management and fulfillment for ordering restaurants.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """
    source = intent_request['invocationSource']
    
    if source != 'FulfillmentCodeHook':
        raise Exception('Sorry, we are in the wrong stage')

    restaurant_type = get_slots(intent_request)["RestaurantType"]
    date = get_slots(intent_request)["DiningDate"]
    time = get_slots(intent_request)["DiningTime"]
    size = get_slots(intent_request)["PeopleNum"]
    phone = get_slots(intent_request)["PhoneNum"]
    location = get_slots(intent_request)["Location"]
    price = get_slots(intent_request)["Price"]
    
    
    # Order the restaurants, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.
    send_SQS(intent_request, 'DiningSuggestion')
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thanks. You will receive a message on your phone short after.'})


""" --- Intents --- """

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestions':
        return send_sqs_message(intent_request)
    else:
        raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Send message to SQS --- """

def send_SQS(intent_request, SQS):
    message = get_slots(intent_request)
    # Get the service resource
    sqs = boto3.resource('sqs')

    # Get the queue
    queue = sqs.get_queue_by_name(QueueName = SQS)

    # Create a new message
    queue.send_message(MessageBody = json.dumps(message))



""" --- Main handler --- """

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
