# def lambda_handler(event, context):
#     # TODO implement
#     if event["messages"][0]["unstructured"]["text"] == "Hello":
#         return "Hi, how can I help you with?"
#     else:
#         return "Hi, I am glad to help!"
import boto3
def lambda_handler(event, context):
    user_id = event["messages"][0]["unstructured"]["id"]
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='DiningSuggestion',
        botAlias='myApp',
        userId=user_id,
        sessionAttributes={},
        requestAttributes={},
        inputText = event["messages"][0]["unstructured"]["text"]
    )
    return response["message"]