""" Operate the registry service """

import os
import requests
import voithos.lib.util.util as util
from click import echo
from colorama import Fore, Style
from voithos.constants import KOLLA_IMAGE_REPOS
from voithos.lib.system import shell, error


def start(ip_address, port):
    """ Start the local registry """
    shell(f"docker run -d --name registry -p {ip_address}:{port}:5000 registry:2")


def offline_start(ip_address, port, path):
    """ Load and start offline registry """
    if not os.path.exists(path):
        error(f"{Fore.RED}ERROR: Registry image not found at {path}{Style.RESET_ALL}", exit=True)
    else:
       shell(f"docker load --input {path}")
       filename = path.rsplit("/", 1)[1]
       image_name_tag = filename_to_image_name_tag(filename)
       shell(f"docker run -d --name registry -p {ip_address}:{port}:5000 {image_name_tag}")

def sync_offline_images(kolla_tag, bw_tag, ceph_release, path, keep, registry):
    """ Sync registry with offline images"""
    if kolla_tag not in KOLLA_IMAGE_REPOS:
        error(f"ERROR: release {kolla_tag} is not supported", exit=True)
    all_kolla_tag_images = KOLLA_IMAGE_REPOS[kolla_tag]
    kolla_tag_service_images = ["pip", "apt", "openstack-client", "kolla-ansible"]
    all_kolla_tag_images.extend(kolla_tag_service_images)
    image_count = len(KOLLA_IMAGE_REPOS[kolla_tag])
    index = 1
    echo("Syncing images with tag: {}".format(kolla_tag))
    for repo in all_kolla_tag_images:
        echo(f"Progress: {index}/{image_count} - Image: {repo}")
        _sync_image(repo, kolla_tag, keep, registry, path)
        index += 1
    index = 1
    all_bw_tag_images = ["rsyslog", "pxe", "arcus-api", "arcus-client", "arcus-mgr"]
    image_count = len(all_bw_tag_images)
    echo("Syncing images with tag: {}".format(bw_tag))
    for repo in all_bw_tag_images:
        echo(f"Progress: {index}/{image_count} - Image: {repo}")
        _sync_image(repo, bw_tag, keep, registry, path)
        index += 1
    echo("Syncing ceph-ansible image")
    _sync_image("ceph-ansible", ceph_release, keep, registry, path)

def sync_offline_single_image(name, tag, path, keep, registry):
    """ Sync registry with offline image"""
    echo("Syncing Image breqwatr/{}:{} with {}".format(name, tag, registry))
    _sync_image(name, tag, keep, registry, path)

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

def _sync_image(image_name, tag, keep, registry, path):
    """ Load, tag and push offline image to registry """
    image_name_tag = f"breqwatr/{image_name}:{tag}"
    registry_image_name_tag = f"{registry}/{image_name_tag}"
    image_path = path
    if not image_path.endswith(".docker"):
        image_path = util.get_image_filename_path(image_name_tag, path)
    if not os.path.exists(image_path):
       error(f"{Fore.RED}ERROR: Image path {image_path} doesn't exist{Style.RESET_ALL}", exit=False)
       return
    shell(f'docker load --input {image_path}')
    shell(f"docker tag {image_name_tag} {registry_image_name_tag}")
    shell(f"docker push {registry_image_name_tag}")
    echo("Done syncing {}".format(registry_image_name_tag))
    if not keep:
        echo(f"Deleting local images {image_name_tag} and {registry_image_name_tag}")
        shell(f"docker rmi {image_name_tag}")
        shell(f"docker rmi {registry_image_name_tag}")

def filename_to_image_name_tag(filename):
    """ Get image name and tag using image filename"""
    filename = filename.replace(".docker", "")
    name_tag_list = filename.rsplit("-", 1)
    name = name_tag_list[0].replace("-", "/", 1)
    tag = name_tag_list[1]
    name_and_tag = name+":"+tag
    return name_and_tag
