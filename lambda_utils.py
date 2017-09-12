"""Utilities for lambda handler"""
import os

from base64 import b64decode

import boto3

def kms_decrypt_env(key):
    """Decrypt environment variable"""
    return kms_decrypt(os.environ[key])

def kms_decrypt(encrypted_data):
    """Decrypt KMS variables"""
    res = boto3.client('kms').decrypt(
        CiphertextBlob=b64decode(encrypted_data),
    )
    return res['Plaintext']

def s3_bucket_for(bucket_prefix, path):
    """returns s3 bucket for path"""
    suffix = s3_bucket_suffix_for(path)
    return "{}-{}".format(bucket_prefix, suffix)


def s3_bucket_suffix_for(path):
    """returns bucket suffix for product delivery paths"""
    path = path.lstrip("/")
    if (path.startswith("pub/firefox/bundles/") or
            path.startswith("pub/firefox/try-builds/")):
        return "archive"

    if path.startswith("pub/firefox/"):
        return "firefox"

    if (path.startswith("pub/labs/") or
            path.startswith("pub/webtools/") or
            path.startswith("pub/nspr/") or
            path.startswith("pub/security")):
        return "contrib"

    return "archive"
