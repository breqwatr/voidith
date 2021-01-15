""" Utils Library"""
import docker
import os
import pkg_resources
import sys
import subprocess
import voithos.lib.aws.ecr as ecr
import voithos.lib.aws.s3 as s3
from click import echo
from colorama import Fore, Style
from pathlib import Path
from requests.exceptions import ReadTimeout
from voithos.constants import KOLLA_IMAGE_REPOS, OFFLINE_DEPLOYMENT_SERVER_PACKAGES
from voithos.lib.system import error, shell


def verify_create_dirs(path):
    """ Check if path exist and create if it doesn't for offline media"""
    if not os.path.isdir(path):
        echo("Creating base directory: {}".format(path))
        os.mkdir(path)
    image_dir_path = "{}/images/".format(path)
    if not os.path.isdir(image_dir_path):
        echo("Creating images directory: {}".format(image_dir_path))
        os.mkdir(image_dir_path)


def create_and_upload_offline_apt_repo_tar_file():
    """Downloads apt packages and their dependencies
    and create Packages.gz for all downloaded packages.
    Then uploads them to s3.
    """
    packages_list = OFFLINE_DEPLOYMENT_SERVER_PACKAGES
    path = str(Path.home())
    apt_packages_dir = f"{path}/apt_packages"
    echo("Creating base directory: {}".format(apt_packages_dir))
    os.mkdir(apt_packages_dir)
    # 104 is uid of _apt and 0 is gid of root
    os.chown(apt_packages_dir, 104, 0)
    os.chdir(apt_packages_dir)
    shell("apt-get update && apt-get install -y apt-rdepends dpkg-dev")
    for package in packages_list:
        dependencies_list = get_package_dependencies_list(package, apt_packages_dir)
        echo("\nDownloading {} and its dependencies".format(package))
        for dependency in dependencies_list:
            cmd = f"apt-get download {dependency}"
            try:
                subprocess.check_call(cmd, shell=True)
            except subprocess.CalledProcessError as e:
                print(e)
    # Creating Packages.gz containing downloaded packages info
    shell("dpkg-scanpackages ./ /dev/null | gzip -9c > ./Packages.gz")
    shell("cd && tar --remove-files -zcf apt.tar.gz apt_packages")
    tar_file_path = f"{path}/apt.tar.gz"
    s3.upload(tar_file_path, "voithos-files", "apt.tar.gz")


def create_and_upload_offline_voithos_tar_file(voithos_branch):
    """ Creates voithos package, downlaod dependencies and upload them to s3"""
    voithos_requirements = pkg_resources.get_distribution("voithos").requires()
    requirements_str = " ".join(str(i) for i in voithos_requirements)
    home_dir = str(Path.home())
    packages_dir = f"{home_dir}/voithos_packages"
    echo("Creating base directory: {}".format(packages_dir))
    os.mkdir(packages_dir)
    os.mkdir(f"{packages_dir}/dependencies")
    os.chdir(packages_dir)
    requirements_file = open("requirements.txt", "w+")
    for r in requirements_str.split():
        requirements_file.write(f"{r}\n")
    requirements_file.close()
    cmds = (
        f"pip download -r {packages_dir}/requirements.txt -d {packages_dir}/dependencies/ "
        f"&& git clone --branch {voithos_branch} https://github.com/breqwatr/voithos.git "
        f"&& cd {packages_dir}/voithos "
        f"&& python3 setup.py sdist "
        f"&& mv {packages_dir}/voithos/dist/voithos*tar.gz {packages_dir} "
        f"&& cd {packages_dir} "
        f"&& rm -r {packages_dir}/voithos "
        f"&& cd && tar --remove-files -zcf voithos.tar.gz voithos_packages"
    )
    shell(cmds)
    tar_file_path = f"{home_dir}/voithos.tar.gz"
    s3.upload(tar_file_path, "voithos-files", "voithos.tar.gz")


def get_package_dependencies_list(package, apt_packages_dir):
    """ Returns a list of package dependencies"""
    output = subprocess.getoutput(f'apt-rdepends {package}|grep -v "^ "')
    if "Unable to locate package" in output:
        shell(f"rm -r {apt_packages_dir}")
        error(f"{Fore.RED}ERROR: Unable to locate package: {package}{Style.RESET_ALL}", exit=True)
    dependencies = subprocess.check_output(
        f'apt-rdepends {package}|grep -v "^ "', shell=True
    ).decode("utf-8")
    return dependencies.replace("\n", " ").split()


def pull_and_save_kolla_tag_images(kolla_tag, path, force):
    """ Pull and save kolla and service images with kolla tag"""
    if kolla_tag not in KOLLA_IMAGE_REPOS:
        error(
            f"{Fore.RED}ERROR: kolla tag {kolla_tag} is not supported{Style.RESET_ALL}", exit=True
        )
    all_images = KOLLA_IMAGE_REPOS[kolla_tag]
    kolla_tag_service_images = ["pip", "apt", "openstack-client", "kolla-ansible"]
    all_images.extend(kolla_tag_service_images)
    image_dir_path = "{}/images/".format(path)
    echo("Pulling dockerhub images with tag: {}\n".format(kolla_tag))
    _pull_and_save_all(all_images, kolla_tag, image_dir_path, force)


def pull_and_save_bw_tag_images(bw_tag, path, force):
    """ Pull and save service images with bw tag"""
    bw_tag_docker_images = ["rsyslog", "pxe", "registry"]
    bw_tag_ecr_images = ["arcus-api", "arcus-client", "arcus-mgr"]
    image_dir_path = "{}/images/".format(path)
    echo("Pulling dockerhub images with tag: {}\n".format(bw_tag))
    _pull_and_save_all(bw_tag_docker_images, bw_tag, image_dir_path, force)
    echo("Pulling ecr images with tag: {}\n".format(bw_tag))
    _pull_and_save_all_ecr(bw_tag_ecr_images, bw_tag, image_dir_path, force)


def pull_and_save_single_image(image_name, tag, path, force):
    """ Pull and save any image from dockerhub breqwatr repo or ecr """
    image_name = f"breqwatr/{image_name}:{tag}"
    if "arcus" in image_name:
        pull_ecr(image_name)
    else:
        pull(image_name)
    save(image_name, path, force)


def _pull_and_save_all(image_name_list, tag, path, force):
    """ Pull and save bw dockerhub images"""
    i = 1
    count = len(image_name_list)
    for image in image_name_list:
        image_name = f"breqwatr/{image}:{tag}"
        echo("Pulling image {} of {}\t{}".format(i, count, image_name))
        i += 1
        pull(image_name)
        save(image_name, path, force)


def _pull_and_save_all_ecr(image_name_list, tag, path, force):
    """ Pull and save ecr images"""
    i = 1
    count = len(image_name_list)
    for image in image_name_list:
        image_name = f"breqwatr/{image}:{tag}"
        echo("Pulling image {} of {}\t{}".format(i, count, image_name))
        i += 1
        pull_ecr(image_name)
        save(image_name, path, force)


def pull(image_name_tag):
    """ Pull single image from bw dockerhub """
    try:
        shell(f"docker pull {image_name_tag}")
    except:
        error(f"{Fore.RED}ERROR: Image {image_name_tag} not found{Style.RESET_ALL}", exit=False)


def pull_ecr(image_name_tag):
    """ Pull single image from ecr """
    try:
        ecr.pull(image_name_tag)
    except:
        error(f"{Fore.RED}ERROR: Image {image_name_tag} not found{Style.RESET_ALL}", exit=False)


def save(image_name_tag, images_dir_path, force):
    """ Save docker image to offline path """
    client = docker.from_env()
    try:
        image = client.images.get(image_name_tag)
    except docker.errors.ImageNotFound:
        return
    image_path = get_image_filename_path(image_name_tag, images_dir_path)
    if os.path.exists(image_path) and not force:
        error(
            f"{Fore.YELLOW}Warning: {image_name_tag} already exists: use --force to overwrite.{Style.RESET_ALL}",
            exit=False,
        )
        return
    echo("Saving: {}".format(image_path))
    try:
        with open(image_path, "wb") as _file:
            for chunk in image.save(named=image_name_tag):
                _file.write(chunk)
    except ReadTimeout:
        # Sometimes Docker will time out trying to export the image
        err = "Docker timeout trying to export file. Check CPU usage?\n"
        sys.stderr.write(f"{Fore.RED}ERROR: {err}{Style.RESET_ALL}\n")
    if os.path.exists(image_path):
        # If ReadTimeout leaves a 0b file behind
        if os.path.getsize(image_path) == 0:
            sys.stderr.write("WARN: Removing empty file {}\n".format(image_path))
            os.remove(image_path)
        else:
            os.chmod(image_path, 0o755)
    else:
        sys.stderr.write(f"{Fore.RED}ERROR: Failed to create {image_path}{Style.RESET_ALL}\n")


def get_image_filename_path(image_name_tag, images_dir_path):
    """ Get path to image file"""
    image_filename = image_name_tag.replace("/", "-").replace(":", "-")
    images_dir_path = images_dir_path.rstrip("/")
    image_path = f"{images_dir_path}/{image_filename}.docker"
    return image_path
