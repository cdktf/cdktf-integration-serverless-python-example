import asyncio
import json
import uuidv
from datetime import datetime
from aws_lambda_powertools.utilities.data_classes import event_source, APIGatewayProxyEventV2
import posts as storage


def json_response(event):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(event["body"])
    }

async def getAllPosts():
    return {
        "body": {
            "data": await storage.getAllPosts()
        }
    }

async def getPost(id: str):
    return {
        "body": await storage.getPost(id)
    }

async def postPost(event: APIGatewayProxyEventV2):
    post = json.loads(event.body)
    await storage.addPost({
        "id": uuidv.uuid4().__str__(),
        "postedAt": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        "author": post["author"],
        "content": post["content"]
    })
    return {
        "statusCode": 201,
        "body": {},
    }


async def async_lambda_handler(event: APIGatewayProxyEventV2, context):
    method = event.http_method
    path = event.path
    try:
        if(path == "/posts"):
            if(method == "GET"):
                return json_response(await getAllPosts())
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
            matches = path.split("/")[1:]
            if(matches):
                if(method == "GET"):
                    return json_response(await getPost(matches[1]))
                else:
                    return json_response({
                        "statusCode": 405,
                        "body": {"error": "Method {methodArg} not supported on {pathArg}".format(methodArg = method, pathArg = path) },
                    })
        return json_response({
            "statusCode": 404,
            "body": {"error": "No matching route found"}
        })
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print("HANDLER ERROR MESSAGE")
        print(message)
        return json_response({
            "statusCode": 500,
            "body": {"error": "request failed"}
        })

@event_source(data_class=APIGatewayProxyEventV2)
def lambda_handler(event: APIGatewayProxyEventV2, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_lambda_handler(event,context))