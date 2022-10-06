import os
import os.path as Path
import json
from constructs import Construct
from cdktf import TerraformAsset, AssetType
from cdktf_cdktf_provider_aws.dynamodb_table import DynamodbTable
from cdktf_cdktf_provider_aws.iam_role import IamRole, IamRoleInlinePolicy
from cdktf_cdktf_provider_aws.iam_role_policy_attachment import IamRolePolicyAttachment
from cdktf_cdktf_provider_aws.lambda_function import LambdaFunction, LambdaFunctionEnvironment
from cdktf_cdktf_provider_aws.lambda_permission import LambdaPermission
from cdktf_cdktf_provider_aws.apigatewayv2_api import Apigatewayv2Api, Apigatewayv2ApiCorsConfiguration


class PostsApi(Construct):

    apiEndPoint: str
    
    def __init__(self, scope: Construct, id: str, environment: str, table: DynamodbTable, userSuffix: str):
        super().__init__(scope,id)

        role = IamRole(self, "lambda-exec",
            name = f"sls-example-post-api-lambda-exec-{userSuffix if userSuffix is not None else ''}",
            assume_role_policy = json.dumps({
                "Version": "2012-10-17",
                "Statement": 
                    {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "lambda.amazonaws.com",
                    },
                    "Effect": "Allow",
                    "Sid": "",
                    },
            }),
            inline_policy = [
                IamRoleInlinePolicy(
                    name = "AllowDynamoDB",
                    policy = json.dumps({
                        "Version": "2012-10-17",
                        "Statement": 
                        {
                            "Action": [
                            "dynamodb:Scan",
                            "dynamodb:Query",
                            "dynamodb:BatchGetItem",
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            ],
                            "Resource": table.arn,
                            "Effect": "Allow",
                        },
                    }) 
                )
            ],    
        )

        IamRolePolicyAttachment(self, "lambda-managed-policy",
            policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            role = role.name,
        )

        asset = TerraformAsset(self, "lambda-asset",
            path = Path.join(os.getcwd(), "posts/api/lambdaPy"),
            type = AssetType.ARCHIVE,
        )

        new_lambda = LambdaFunction(self, "api",
            function_name = f"sls-example-posts-api-{userSuffix if userSuffix is not None else ''}",
            handler = "index.lambda_handler",
            runtime = "python3.9",
            role = role.arn,
            filename = asset.path,
            source_code_hash = asset.asset_hash,
            environment =  LambdaFunctionEnvironment(
                variables = {"DYNAMODB_TABLE_NAME":table.name}
            )
        )

        api = Apigatewayv2Api(self, "api-gw",
            name = f"sls-example-posts-{userSuffix if userSuffix is not None else ''}",
            protocol_type = "HTTP",
            target = new_lambda.arn,
            cors_configuration = Apigatewayv2ApiCorsConfiguration(
                allow_origins = ["*"],
                allow_methods = ["*"],
                allow_headers = ["*"]
            )
        )
        self.apiEndPoint = api.api_endpoint

        LambdaPermission(self, "apigw-lambda",
            function_name = new_lambda.function_name,
            action = "lambda:InvokeFunction",
            principal = "apigateway.amazonaws.com",
            source_arn = "{}/*/*".format(api.execution_arn)
        )
        
        
    