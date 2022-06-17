import asyncio
import json
import os
import re
import boto3
from datetime import datetime
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
import posts as storage

app = APIGatewayHttpResolver()

def json_response(event):
    print(APIGatewayProxyEvent({
        "statusCode": 200,
        #**event,
        "headers": {
            #**event["headers"], 
            "Content-Type": "application/json"
        },
        "body": json.dumps(event["body"])
    }))
    return APIGatewayProxyEvent({
        "statusCode": 200,
        #**event,
        "headers": {
            #**event["headers"], 
            "Content-Type": "application/json"
        },
        "body": json.dumps(event["body"])
    })

@app.get("/posts")
def pls(event):
    return {
        "data": json.dumps(event["body"])
    }

async def getAllPosts(event):
    return {
        "body": {
            "data": await storage.getAllPosts()
        }
    }

async def getPost(id: str, event):
    return {
        "body": await storage.getPost(id)
    }

async def postPost(event):
    await storage.addPost({
        "id": event["body"]["id"],
        "postedAt": datetime.date(),
        "author": event["body"]["author"],
        "content": event["body"]["content"],
    })
    return {
        "statusCode": 201,
        "body": {},
    }

async def async_lambda_handler(event, context):
    event = APIGatewayProxyEvent(event)
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]
    #try:
    if(path == "/posts"):
        if(method == "GET"):
            return pls(await getAllPosts(event))
        if(method == "POST"):
            return json_response(await postPost(event))
        if(method == "OPTIONS"):
            return {"statusCode": 200}
        else:
            return json_response({
                "statusCode": 405,
                "body": {"error": "Method {methodArg} not supported on {pathArg}".format(methodArg = method, pathArg = path) },
            })
    if(path.startswith("/posts")):
        matches = re.findall(r'/^\/posts\/([^\/]+)\/detail$/', path)
        if(len(matches) > 0):
            if(method == "GET"):
                return json_response(await getPost(matches[1], event))
            else:
                return json_response({
                    "statusCode": 405,
                    "body": {"error": "Method {methodArg} not supported on {pathArg}".format(methodArg = method, pathArg = path) },
                })
    return json_response({
        "statusCode": 404,
        "body": {"error": "No matching route found"}
    })
    #except:
    #    return json_response({
    #        "statusCode": 500,
    #        "body": {"error": "request failed"}
    #    })

def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_lambda_handler(event,context))


