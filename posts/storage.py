from cdktf_cdktf_provider_aws.dynamodb_table import DynamodbTable, DynamodbTableAttribute
from constructs import Construct

class PostsStorage(Construct):

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