""" Library for AWS Elastic Container Registry

    Breqwatr stores our private images in ECR then retags them to strip the ecr prefix so they look
    nice in the Docker image list.
"""

from base64 import b64decode

import botocore.exceptions

import voithos.lib.aws.aws as aws
from voithos.lib.system import shell, error


def get_ecr_config():
    """ decode and parse ECR token into usable dict """
    client = aws.get_client("ecr")
    try:
        token = client.get_authorization_token()
    except botocore.exceptions.ClientError as exc:
        error(exc)
        error("ERROR: Failed connecting to the private registry (invalid key)", exit=True)
    url = token["authorizationData"][0]["proxyEndpoint"]
    decoded_auth_token = b64decode(token["authorizationData"][0]["authorizationToken"])
    username, password = tuple(decoded_auth_token.decode("utf-8").split(":"))
    registry = url.replace("https://", "").replace("http://", "")
    credentials = {"username": username, "password": password, "url": url, "registry": registry}
    return credentials


def login():
    """ Log into ECR """
    ecr_data = get_ecr_config()
    username = ecr_data["username"]
    password = ecr_data["password"]
    server = ecr_data["url"]
    shell(f"docker login --username {username} --password {password} {server}", print_cmd=False)


def pull(image):
    """ Pull an image from ECR & strip the AWS prefix """
    login()
    ecr_data = get_ecr_config()
    registry = ecr_data["registry"]
    ecr_image = f"{registry}/{image}"
    shell(f"docker pull {ecr_image}", print_cmd=False)
    shell(f"docker tag {ecr_image} {image}", print_cmd=False)
    shell(f"docker rmi {ecr_image}", print_cmd=False)
