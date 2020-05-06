""" AWS calls """

import boto3

import voithos.lib.config as config
from voithos.lib.system import error


def get_aws_iam():
    """ Extract AWS IAM credentials from the license key """
    config.require_license()
    license = config.get_license()
    if len(license) != 61 or license[20] != "-":
        error(f"ERROR: The license {license} is invalid", exit=True)
    iam_id = license[0:20]
    iam_secret = license[21:61]
    return {"id": iam_id, "secret": iam_secret}


def get_client(name):
    """ decode and parse ECR token into usable dict """
    iam = get_aws_iam()
    session = boto3.Session(aws_access_key_id=iam["id"], aws_secret_access_key=iam["secret"])
    client = session.client(name, region_name="ca-central-1")
    return client
