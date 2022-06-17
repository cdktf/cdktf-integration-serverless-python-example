from cdktf import Resource
from constructs import Construct
from posts.api.index import PostsApi
from posts.storage import PostsStorage

class Posts(Resource):

    #maybe express in way that show its the same type as the endpoint in PostsApi
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