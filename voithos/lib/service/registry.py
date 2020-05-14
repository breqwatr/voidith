""" Operate the registry service """

import requests
from click import echo

from voithos.lib.system import shell, error


def start(ip_address, port):
    """ Start the local registry """
    shell(f"docker run -d --name registry -p {ip_address}:{port}:5000 registry:2")


def list_images(registry):
    """ Print the images in a registry """
    catalog = f"{registry}/v2/_catalog"
    try:
        response = requests.get(url=catalog)
    except requests.exceptions.ConnectionError:
        error(f"ERROR: Failed to connect to {registry}. Is the port correct?", exit=True)
    repositories = response.json()["repositories"]
    for repository in repositories:
        echo(repository)
        tags_url = f"{registry}/v2/{repository}/tags/list"
        tag_resp = requests.get(url=tags_url)
        resp_json = tag_resp.json()
        if "tags" in resp_json:
            tags = resp_json["tags"]
            for tag in tags:
                echo(f" - {tag}")
        if "errors" in resp_json:
            for err in resp_json["errors"]:
                err_code = err["code"]
                err_msg = err["message"]
                error(f"  WARNING: {err_code} - {err_msg}", exit=False)
