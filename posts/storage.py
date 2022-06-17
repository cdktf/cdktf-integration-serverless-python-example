from unicodedata import name
from cdktf_cdktf_provider_aws.dynamodb import DynamodbTable, DynamodbTableAttribute
from cdktf import Resource
from constructs import Construct

class PostsStorage(Resource):

    table: DynamodbTable

    def __init__(self, scope: Construct, id: str, environment: str, userSuffix: str):
        super().__init__(scope,id)

        self.table = DynamodbTable(self, "table",
            name = f"sls-posts-{userSuffix if userSuffix is not None else ''}",
            billing_mode = "PAY_PER_REQUEST",
            hash_key = "id",
            range_key = "postedAt",
            attribute = [
                DynamodbTableAttribute(
                    name = "id",
                    type = "S"
                ),
                DynamodbTableAttribute(
                    name = "postedAt",
                    type = "S"
                )
            ]
        )