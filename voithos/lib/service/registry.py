""" Operate the registry service """

import os
import requests

from click import echo
from colorama import Fore, Style
from voithos.lib.system import shell, error


def start(ip_address, port):
    """ Start the local registry """
    shell(f"docker run -d --name registry -p {ip_address}:{port}:5000 registry:2")


def offline_start(ip_address, port, path):
    if not os.path.exists(path):
        error(f"{Fore.RED}ERROR: Registry image not found at {path}{Style.RESET_ALL}", exit=True)
    else:
       shell(f"docker load --input {path}")
       filename = path.rsplit("/", 1)[1]
       image_name_tag = filename_to_image_name_tag(filename)
       shell(f"docker run -d --name registry -p {ip_address}:{port}:5000 {image_name_tag}")
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

# breqwatr-registry-2.docker
def filename_to_image_name_tag(filename):
    filename = filename.replace(".docker", "")
    name_tag_list = filename.rsplit("-", 1)
    name = name_tag_list[0].replace("-", "/", 1)
    tag = name_tag_list[1]
    name_and_tag = name+":"+tag
    return name_and_tag
