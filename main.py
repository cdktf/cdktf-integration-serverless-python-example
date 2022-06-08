#!/usr/bin/env python
import string
import cdktf
from cdktf_cdktf_provider_aws import AwsProvider
from cdktf_cdktf_provider_local import LocalProvider
from constructs import Construct
from cdktf import App, TerraformStack
from cdktf import Resource, TerraformOutput
from frontend.index import Frontend



class FrontendStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str, apiEndPoint: str):
        super().__init__(scope, ns)

        AwsProvider(self, "aws",
            region = "eu-central-1",
        )
        LocalProvider(self, "local")
        Frontend(self, "frontend", 
            environment = "dev",
            apiEndPoint = "",
        )

        # define resources here
        


app = App()
FrontendStack(app, "frontend-dev", "")

app.synth()
