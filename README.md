# CDK for Terraform Serverless Application in Python

_This repository was created for demo purposes and will not be kept up-to-date with future releases of CDK for Terraform (CDKTF); as such, it has been archived and is no longer supported in any way by HashiCorp. You are welcome to try out the archived version of the code in this example project, but there are no guarantees that it will continue to work with newer versions of CDKTF. We do not recommend directly using this sample code in production projects without extensive testing, and HashiCorp disclaims any and all liability resulting from use of this code._

-----

This repository contains an end to end serverless web app hosted on AWS and deployed with [CDK for Terraform](https://cdk.tf) in Python. In more application specific terms, we are deploying serverless infrastructure for a web app that has a list of posts and a modal to create a new post by specifying author and content. For more information regarding setup and the features of CDKTF [please refer to these docs](https://www.terraform.io/cdktf).

## Local Usage

### Prerequisites

In order to run this example you must have CDKTF and it's prerequisites installed. For further explanation please see [this quick start demo](https://learn.hashicorp.com/tutorials/terraform/cdktf-install?in=terraform/cdktf).

Additionally an AWS account and [AWS credentials configured for use with Terraform](https://learn.hashicorp.com/tutorials/terraform/cdktf-install?in=terraform/cdktf) are needed.

### To Deploy

First run `pipenv install` in the root directory of the project to create a virtual environment with all the needed packages installed.  

Then in that virtual environment `cdktf deploy` can be runned with the stacks that you wish to deploy e.g `cdktf deploy posts-dev frontend-dev` for deploying the dev environement or `cdktf deploy posts-prod frontend-prod` for deploying the production environment.

## Techstack

Frontend: React, Create React App, statically hosted via AWS S3 + CloudFront
Backend API: AWS Lambda + API Gateway + DynamoDB

## Application

### Stacks

We will have two primary Stacks– PostsStack and FrontendStack

The Post and Frontend class encapsulate the finer details of infrastructure provisioned for each respective Stack. The first parameter denotes the scope of the infrastructure being provision– we use `self` to tie the infrastructure contained in Post/Frontend to the Stack in which it is contained, the same is true with `AwsProvider`.

```python
class PostsStack(TerraformStack):

   posts: Posts

   def __init__(self, scope: Construct, name: str, environment: str, user: str):
       super().__init__(scope,name)

       AwsProvider(self, "aws",
           region =  "eu-central-1",
       )

       self.posts = Posts(self, "posts",
           environment = environment,
           userSuffix = user
       )

```

```python
class FrontendStack(TerraformStack):

   def __init__(self, scope: Construct, name: str, environment: str , apiEndPoint: str):
       super().__init__(scope, name)

       AwsProvider(self, "aws",
           region = "eu-central-1",
       )
       LocalProvider(self, "local")
       Frontend(self, "frontend",
           environment = environment,
           apiEndPoint = apiEndPoint,
       )

```

In using different Stacks to separate aspects of our infrastructure we allow for separation in state management of the frontend and backend– making alteration and redeployment of a specific piece of infrastructure a simpler process. Additionally, this allows for the instantiation of the same resource multiple times throughout.

For example…

```python
# In main.py

postsDev = PostsStack(app, "posts-dev",
       environment = "development",
       user = os.getenv("CDKTF_USER")
   )
frontendDev = FrontendStack(app, "frontend-dev",
       environment = "development",
       apiEndPoint = postsDev.posts.apiEndPoint,
   )
postsProd = PostsStack(app, "posts-prod",
       environment = "production",
       user = os.getenv("CDKTF_USER")
   )
frontendProd = FrontendStack(app, "frontend-prod",
       environment = "production",
       apiEndPoint = postsProd.posts.apiEndPoint,
   )`
```

Here we created separate instances of the infrastructure for the frontend and backend with different naming of the resources in each application environment (by ways of the environment param), with the ease of adding additional as needed.

### Posts

The Posts class melds two elements together– the Dynamodb table coming from PostsStorage and our Lambda function and Apigateway coming from PostsApi that takes our new Dynamodb table for setting up the Lambda function environment.

```python
class Posts(Resource):

   apiEndPoint: str

   def __init__(self, scope: Construct, id: str, environment: str, userSuffix: str ):
       super().__init__(scope, id)

       storage = PostsStorage(self, "storage",
           environment = environment,
           userSuffix = userSuffix
       )

       postsApi = PostsApi(self, "api",
           environment = environment,
           table = storage.table,
           userSuffix = userSuffix
       )

       self.apiEndPoint = postsApi.apiEndPoint

```

In PostsApi we create our Lambda function and Apigateway, along with the needed permissions/policies and IAM role.

Here we see a use of the environment variable– the one that was initially given in main.java. With this we provide greater description for the resources in each environment as well as avoiding naming conflicts.

```python
       role = IamRole(self, "lambda-exec",
           name = f"sls-example-post-api-lambda-exec-{userSuffix if userSuffix is not None else ''}",
//...
```

It is also in the IAM Role that we define certain policies for the role. It is important to note that policies that are denoted as taking Strings (in IamRole and elsewhere) are really JSON strings.

For example…

```python
role = IamRole(self, "lambda-exec",
		   #...
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
		   #...
```

This TerraformAsset helps manage our local Lambda function implementation. Providing necessary details for defining our Lambda.

```python
asset = TerraformAsset(self, "lambda-asset",
           path = Path.join(os.getcwd(), "posts/api/lambdaPy"),
           type = AssetType.ARCHIVE,
       )
```

Now we get into the details of our Lambda function. It is here that we provide the Lambda with the role we created above as well as the Dynamodb table from the Storage object created alongside this PostsApi object in the Post class. We also provide other needed details (name of handler, runtime, local path to lambda implementation, ect.).

```python
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
```

Our API Gateway will sit between our Frontend and Lambda function– both routing requests to our Lambda as well as returning the appropriate result. We give the API Gateway our Lambda function defined as its target.

```python
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

```

We then pass the API Gateway’s endpoint to the PostApi object– this will be later given to our Frontend.

```python
self.apiEndPoint = api.api_endpoint
```

Finally we provide Permissions to our Lambda and additional policy for our IAM Role.

```python
IamRolePolicyAttachment(self, "lambda-managed-policy",
           policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
           role = role.name,
       )

#...

LambdaPermission(self, "apigw-lambda",
           function_name = new_lambda.function_name,
           action = "lambda:InvokeFunction",
           principal = "apigateway.amazonaws.com",
           source_arn = "{}/*/*".format(api.execution_arn)
       )

```

### Frontend

In the Frontend class we provision a S3 Bucket as well as a Cloudfront distribution for our React app to be statically hosted.

```python
bucket = S3Bucket(self, "bucket",
           bucket_prefix = "sls-example-frontend-{}".format(environment),
           tags = {
               "hc-internet-facing": "true"
           }
       )
       bucketWebsite = S3BucketWebsiteConfiguration(self, "website-configuration",
           bucket = bucket.bucket,
           index_document = S3BucketWebsiteConfigurationIndexDocument(suffix = "index.html"),
           error_document = S3BucketWebsiteConfigurationErrorDocument(key = "index.html")
       )
```

The Cloudfront Distribution speeds up the distribution of our Frontend content and reduces the load on our S3 Bucket by caching its contents. It is here we define the behavior and permission of this cache as well as provide the endpoint of the S3 Bucket we defined above.

```python
          cf = CloudfrontDistribution(self, "cf",
           comment = "Serverless example frontend for env={}".format(environment),
           enabled = True,
           default_cache_behavior = CloudfrontDistributionDefaultCacheBehavior(
               allowed_methods = [
                   "DELETE",
                   "GET",
                   "HEAD",
                   "OPTIONS",
                   "PATCH",
                   "POST",
                   "PUT",
               ],
               cached_methods = ["GET", "HEAD"],
               target_origin_id = S3_ORIGIN_ID,
               viewer_protocol_policy = "redirect-to-https",
               forwarded_values = CloudfrontDistributionDefaultCacheBehaviorForwardedValues(
                   query_string = False,
                   cookies = CloudfrontDistributionDefaultCacheBehaviorForwardedValuesCookies(
                       forward = "none",
                   ),
               ),
           ),
           origin = [
               CloudfrontDistributionOrigin(
                   origin_id = S3_ORIGIN_ID,
                   domain_name = bucketWebsite.website_endpoint,
                   custom_origin_config = CloudfrontDistributionOriginCustomOriginConfig(
                       origin_protocol_policy = "http-only",
                       http_port = 80,
                       https_port = 443,
                       origin_ssl_protocols = ["TLSv1.2", "TLSv1.1", "TLSv1"],
                   )
               ),
           ],
           default_root_object = "index.html",
           restrictions = CloudfrontDistributionRestrictions(
               geo_restriction = CloudfrontDistributionRestrictionsGeoRestriction(
                   restriction_type = "none"
               ),
           ),
           viewer_certificate = CloudfrontDistributionViewerCertificate(
               cloudfront_default_certificate = True
           )
       )
```

The file `env.production.local` provides the S3 Bucket and Backend endpoints to our React app.

```python
File(self, "env",
           filename = Path.join(os.getcwd(), "frontend", "code", ".env.production.local"),
           content = "S3_BUCKET_FRONTEND={bucket}\nREACT_APP_API_ENDPOINT={endPoint}".format(bucket = bucket.bucket, endPoint = apiEndPoint)
       )
```

Finally we create a TerraformOutput that gives us the domain name of the application’s frontend.

```python
TerraformOutput(self, "frontend_domainname",
           value = cf.domain_name,
       ).add_override("value", "https://{}".format(cf.domain_name))

```

## License

[Mozilla Public License v2.0](https://github.com/hashicorp/cdktf-integration-serverless-python-example/blob/main/LICENSE)
