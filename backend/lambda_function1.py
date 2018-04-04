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


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }
    

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


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')
        
        
def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def validate_order_restaurants(restaurant_type, date, location, size, time, phone, price):
    restaurant_types = ['chinese', 'japanese', 'indian', 'french', 'american', 'italian', 'vegetarian', 'halal']
    #price_list = ['pork', 'milk', 'egg', 'wheat', 'none']
    if restaurant_type is not None and restaurant_type.lower() not in restaurant_types:
        return build_validation_result(False,
                                       'RestaurantType',
                                       'We do not have {} restaurants, would you like a different type of restaurant?  '
                                       'Our most popular restaurants are Japanese ones'.format(restaurant_type))
    
    if price is not None and price < 1 and price > 4:
        return build_validation_result(False,
                                       'Price',
                                       'We do not have {} as a choise, the price level should be from 1 to 4. Please input the price preferance again.'.format(price))

    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'DiningDate', 'I did not understand that, what date would you like to go?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'DiningDate', 'You can search for restaurants from now onwards.  What day would you like to have the meal?')

    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        if hour < 8 or hour > 22:
            # Outside of business hours
            return build_validation_result(False, 'DiningTime', 'The business hours of restaurants are from 8 a m. to 23 p m. Can you specify a time during this range?')
            
    if phone is not None:
        phone = ''.join(e for e in phone if e.isdigit())
        if len(phone) != 10:
            return build_validation_result(False, 'PhoneNum', 'Do you wanna try a different phone number with 10 digits?')
    
    if size is not None and size < 1:
        return build_validation_result(False, 'PeopleNum', 'Invalid number. Please tell me the number of people.')
    
    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """

def order_restaurants(intent_request):
    """
    Performs dialog management and fulfillment for ordering restaurants.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """
    
    restaurant_type = get_slots(intent_request)["RestaurantType"]
    date = get_slots(intent_request)["DiningDate"]
    time = get_slots(intent_request)["DiningTime"]
    size = get_slots(intent_request)["PeopleNum"]
    phone = get_slots(intent_request)["PhoneNum"]
    location = get_slots(intent_request)["Location"]
    price = get_slots(intent_request)["Price"]
    source = intent_request['invocationSource']
    
    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_order_restaurants(restaurant_type, date, location, size, time, phone, price)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        # Pass the price of the restaurants back through session attributes to be used in various prompts defined
        # on the bot model.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        #if restaurant_type is not None:
        #    output_session_attributes['Price'] = len(restaurant_type) * 5  # Elegant pricing model
    
        return delegate(output_session_attributes, get_slots(intent_request))
    
    # Order the restaurants, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.
    
    send_SQS(intent_request, 'DiningSuggestion')
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thanks. You will receive a message on your phone short after.'})


def thanks(intent_request):
    thank_message = {
        'contentType': 'PlainText',
        'content': 'No problem. Have a nice day.'
    }
    return close(intent_request['sessionAttributes'], 'Fulfilled', thank_message)
    

def greetings(intent_request):
    greeting_message = {
        'contentType': 'PlainText',
        'content': 'Hi~ How can I help you?'
    }
    return close(intent_request['sessionAttributes'], 'Fulfilled', greeting_message)
    

""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestions':
        return order_restaurants(intent_request)
    elif intent_name == 'Greeting':
        return greetings(intent_request)
    elif intent_name == 'ThankYou':
        return thanks(intent_request)
    else:
        raise Exception('Intent with name ' + intent_name + ' not supported')


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
