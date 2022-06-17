#!/usr/bin/env python
import os
from cdktf_cdktf_provider_aws import AwsProvider
from cdktf_cdktf_provider_local import LocalProvider
from constructs import Construct
from cdktf import App, NamedRemoteWorkspace, RemoteBackend, TerraformStack
from frontend.index import Frontend
from posts.index import Posts


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

class PreviewStack(TerraformStack):

    def __init__(self, scope: Construct, name: str, previewBuildIdentifier: str):
        super().__init__(scope, name)

        posts = Posts(self, "posts",
            environment = previewBuildIdentifier, 
        )
        Frontend(self, "frontend",
            environment = previewBuildIdentifier,
            apiEndPoint = posts.apiEndpoint, 
        )

app = App()

USE_REMOTE_BACKEND = os.getenv("USE_REMOTE_BACKEND") is not None

if(os.getenv("PREVIEW_BUILD_IDENTIFIER") is not None):
    if(os.getenv("PREVIEW_BUILD_IDENTIFIER") in ["development", "production"]):
        raise Exception("environment variable PREVIEW_BUILD_IDENTIFIER may not be set to development or production but it was set to {}".format(os.getenv("PREVIEW_BUILD_IDENTIFIER")))
    PreviewStack(app, "preview",
        previewBuildIdentifier = os.getenv("PREVIEW_BUILD_IDENTIFIER")
    )
else:
    
    postsDev = PostsStack(app, "posts-dev",
        environment = "development",
        user = os.getenv("CDKTF_USER")
    )
    if(USE_REMOTE_BACKEND):
        RemoteBackend(postsDev,
            hostname= "app.terraform.io",
            organization = "terraform-demo-mad",
            workspaces=NamedRemoteWorkspace(name="cdktf-integration-serverless-python-posts-dev")
        )
    
    frontendDev = FrontendStack(app, "frontend-dev",
        environment = "development",
        apiEndPoint = postsDev.posts.apiEndPoint,
    )
    if(USE_REMOTE_BACKEND):
        RemoteBackend(frontendDev,
            hostname= "app.terraform.io",
            organization = "terraform-demo-mad",
            workspaces=NamedRemoteWorkspace(name="cdktf-integration-serverless-python-frontend-dev")
        )
    
    postsProd = PostsStack(app, "posts-prod",
        environment = "production",
        user = os.getenv("CDKTF_USER")
    )
    if(USE_REMOTE_BACKEND):
        RemoteBackend(postsProd,
            hostname= "app.terraform.io",
            organization = "terraform-demo-mad",
            workspaces=NamedRemoteWorkspace(name="cdktf-integration-serverless-python-posts-prod")
        )
    
    frontendProd = FrontendStack(app, "frontend-prod",
        environment = "production",
        apiEndPoint = postsProd.posts.apiEndPoint,
    )
    if(USE_REMOTE_BACKEND):
        RemoteBackend(frontendDev,
            hostname= "app.terraform.io",
            organization = "terraform-demo-mad",
            workspaces=NamedRemoteWorkspace(name="cdktf-integration-serverless-python-posts-prod")
        )

app.synth()