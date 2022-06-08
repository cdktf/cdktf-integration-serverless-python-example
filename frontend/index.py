import json
import os
import os.path as Path
from turtle import forward
from constructs import Construct
from cdktf import Resource, TerraformOutput
from cdktf_cdktf_provider_local import File
from cdktf_cdktf_provider_aws.s3 import S3Bucket, S3BucketPolicy, S3BucketWebsiteConfiguration, S3BucketWebsiteConfigurationIndexDocument, S3BucketWebsiteConfigurationErrorDocument
from cdktf_cdktf_provider_aws.cloudfront import CloudfrontDistribution, CloudfrontDistributionDefaultCacheBehavior, CloudfrontDistributionDefaultCacheBehaviorForwardedValues, CloudfrontDistributionDefaultCacheBehaviorForwardedValuesCookies, CloudfrontDistributionOrigin, CloudfrontDistributionOriginCustomOriginConfig, CloudfrontDistributionRestrictions,CloudfrontDistributionRestrictionsGeoRestriction, CloudfrontDistributionViewerCertificate


S3_ORIGIN_ID = "s3Origin"

class Frontend(Resource):

    def __init__(self, scope: Construct, id: str, environment: str, apiEndPoint: str):
        super().__init__(scope, id)

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

        S3BucketPolicy(self, "s3_policy",
            bucket = bucket.bucket,
            #Might not work 
            policy = json.dumps(
                {
                    "Version": "2012-10-17",
                    "Id": "PolicyForWebsiteEndpointsPublicContent",
                    "Statement": 
                        {
                            "Sid": "PublicRead",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": ["s3:GetObject"],
                            "Resource": ["{}/*".format(bucket.arn), "{}".format(bucket.arn)],
                        },
                }
            ),
        )

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

        File(self, "env",
            filename = Path.join(os.getcwd(), "frontend", "code", ".env.production.local"),
            content = "S3_BUCKET_FRONTEND={bucket}\nREACT_APP_API_ENDPOINT={endPoint}".format(bucket = bucket.bucket, endPoint = apiEndPoint)
        )

        TerraformOutput(self, "frontend_domainname",
            value = cf.domain_name,
        ).add_override("value", "https://{}".format(cf.domain_name))