import os
import boto3
from boto3.dynamodb.conditions import Key

#Add check to check precense of table name env var
if os.environ['DYNAMODB_TABLE_NAME'] is None:
    raise Exception("DYNAMODB_TABLE_NAME env variable is required")

posts_table = boto3.resource('dynamodb').Table(os.environ['DYNAMODB_TABLE_NAME'])

async def getAllPosts():
    result = posts_table.scan(Limit=100)
    return result["Items"]

async def getPost(id: str):
    result = posts_table.query(
        KeyConditionExpression=Key('id').eq(id)
    )
    if(len(result["Items"]) != 1):
        return {}
    return result["Items"][0]

async def addPost(post):
    posts_table.put_item(Item={
        "id": post["id"],
        "postedAt": post["postedAt"],
        "author": post["author"],
        "content": post["content"],

    })