"""AWS Lambda cache clear function handler"""
from urllib.parse import urljoin

import boto3

import akamaiapi
import lambda_utils

AKAMAI_HOSTNAMES = lambda_utils.kms_decrypt_env("AKAMAI_HOSTNAMES").split()

AKAMAI_CLIENT_TOKEN = lambda_utils.kms_decrypt_env("AKAMAI_CLIENT_TOKEN")
AKAMAI_CLIENT_SECRET = lambda_utils.kms_decrypt_env("AKAMAI_CLIENT_SECRET")
AKAMAI_ACCESS_TOKEN = lambda_utils.kms_decrypt_env("AKAMAI_ACCESS_TOKEN")
AKAMAI_BASE_URL = lambda_utils.kms_decrypt_env("AKAMAI_BASE_URL")

CLOUDFRONT_DISTS = lambda_utils.kms_decrypt_env("CLOUDFRONT_DISTS").split()

S3_BUCKET_PREFIX = lambda_utils.kms_decrypt_env("S3_BUCKET_PREFIX")

AKAMAI_SESSION = akamaiapi.Session(
    client_token=AKAMAI_CLIENT_TOKEN,
    client_secret=AKAMAI_CLIENT_SECRET,
    access_token=AKAMAI_ACCESS_TOKEN,
    base_url=AKAMAI_BASE_URL,
)
AKAMAI_API = akamaiapi.API(AKAMAI_SESSION)

CLOUDFRONT_CLIENT = boto3.client('cloudfront')
S3_RESOURCE = boto3.resource('s3')


def lambda_handler(event, context):
    """AWS Lambda handler"""
    paths = event['paths']
    if not isinstance(paths, list):
        raise Exception("paths is not list")

    s3_paths = []
    for path in paths:
        objs = S3_RESOURCE.Bucket(
            lambda_utils.s3_bucket_for(S3_BUCKET_PREFIX, path)
        ).objects.filter(
            Prefix=path,
        )
        s3_paths += [urljoin("/", obj.key) for obj in objs]

    if len(s3_paths) > 10000:
        raise Exception("cannot clear more than 10,000 paths")

    for hostname in AKAMAI_HOSTNAMES:
        resp = AKAMAI_API.cache_invalidate(hostname, paths)


    for dist in CLOUDFRONT_DISTS:
        resp = CLOUDFRONT_CLIENT.create_invalidation(
            DistributionId=dist,
            InvalidationBatch={
                'Quantity': len(paths),
                'Items': paths,
            }
        )
