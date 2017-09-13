"""AWS Lambda cache clear function handler"""
import logging
import os

from urllib.parse import urljoin

import boto3

import akamaiapi
import lambda_utils

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

AKAMAI_HOSTNAMES = os.environ["AKAMAI_HOSTNAMES"].split()

AKAMAI_CLIENT_TOKEN = lambda_utils.kms_decrypt_env("AKAMAI_CLIENT_TOKEN")
AKAMAI_CLIENT_SECRET = lambda_utils.kms_decrypt_env("AKAMAI_CLIENT_SECRET")
AKAMAI_ACCESS_TOKEN = lambda_utils.kms_decrypt_env("AKAMAI_ACCESS_TOKEN")
LOGGER.info(AKAMAI_ACCESS_TOKEN)
AKAMAI_BASE_URL = lambda_utils.kms_decrypt_env("AKAMAI_BASE_URL")

CLOUDFRONT_ROOT_DISTS = os.environ["CLOUDFRONT_ROOT_DISTS"].split()
CLOUDFRONT_DISTS = os.environ["CLOUDFRONT_DISTS"].split()

S3_BUCKET_PREFIX = os.environ["S3_BUCKET_PREFIX"]

AKAMAI_API = akamaiapi.API(
    akamaiapi.Session(
        client_token=AKAMAI_CLIENT_TOKEN,
        client_secret=AKAMAI_CLIENT_SECRET,
        access_token=AKAMAI_ACCESS_TOKEN,
        base_url=AKAMAI_BASE_URL,
    )
)

CLOUDFRONT_CLIENT = boto3.client('cloudfront')
S3_RESOURCE = boto3.resource('s3')


def lambda_handler(event, context):
    """AWS Lambda handler"""
    paths = event['paths']
    if not isinstance(paths, list):
        raise Exception("paths is not list")

    LOGGER.info("Clearing cache for: %s", paths)

    s3_paths = [key for path in paths
                    for key in s3_paths_from_prefix(path)]
    LOGGER.info("Keys found: %s", s3_paths)

    if len(s3_paths) > 10000:
        raise Exception("cannot clear more than 10,000 paths")
    """
    resp = cloudfront_invalidate_and_wait(CLOUDFRONT_ROOT_DISTS, paths,
                                   context.aws_request_id)
    LOGGER.info("Cloudfront Root Invalidations: %s", resp)

    resp = cloudfront_invalidate_and_wait(CLOUDFRONT_DISTS, paths,
                                   context.aws_request_id)
    LOGGER.info("Cloudfront Invalidations: %s", resp)
    """

    if not s3_paths:
        raise Exception("No objects found in s3")

    resp = akamai_invalidate(s3_paths)
    LOGGER.info("Akamai Invalidations: %s", resp)

def akamai_invalidate(paths):
    return [AKAMAI_API.cache_invalidate(hostname, paths)
            for hostname in AKAMAI_HOSTNAMES]

def cloudfront_invalidate_and_wait(dists, paths, call_ref):
    invalidations = [cloudfront_invalidate(dist, paths, call_ref)
                     for dist in dists]
    for invalidation in invalidations:
        cloudfront_wait_invalidation(invalidation)

    return invalidations

def cloudfront_invalidate(dist, paths, call_ref):
        resp = CLOUDFRONT_CLIENT.create_invalidation(
            DistributionId=dist,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths,
                },
                'CallerReference': call_ref,
            }
        )
        return {
            "DistributionId": dist,
            "Id": resp["Invalidation"]["Id"],
        }

def cloudfront_wait_invalidation(invalidation):
    CLOUDFRONT_CLIENT.get_waiter("invalidation_completed").wait(
        DistributionId=invalidation["DistributionId"],
        Id=invalidation["Id"],
        WaiterConfig={
            "Delay": 10,
            "MaxAttempts": 15,
        }
    )


def s3_paths_from_prefix(prefix):
    bucket = lambda_utils.s3_bucket_for(S3_BUCKET_PREFIX, prefix)
    objs = S3_RESOURCE.Bucket(bucket).objects.filter(
        Prefix=prefix.lstrip("/"),
    )
    return [urljoin("/", obj.key) for obj in objs]
