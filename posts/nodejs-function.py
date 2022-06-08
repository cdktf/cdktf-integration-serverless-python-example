import os.path as Path
from cdktf import Resource, TerraformAsset, AssetType
from constructs import Construct

class NodejsFunction(Resource):
    
    def __init__(self, scope: Construct, id: str, path: str):
        super().__init__(scope)