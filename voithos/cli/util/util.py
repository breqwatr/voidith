""" Voithos Utilities """

import click
import os
import voithos.lib.util.util as util
import voithos.lib.aws.s3 as s3
from voithos.cli.util.qemu_img import get_qemu_img_group
from voithos.lib.system import error


@click.option("--kolla-tag", required=True, help="Kolla images tag")
@click.option("--bw-tag", required=True, help="Breqwatr images tag")
@click.option("--ceph-release", required=False, default=None, help="Ceph version")
@click.option(
    "--force/--no-force",
    default=False,
    help="Use --force to overwrite files if they already exists",
)
@click.option("--path", required=True, help="Download path")
@click.command(name="export-offline-media")
def export_offline_media(kolla_tag, bw_tag, ceph_release, force, path):
    """ Download offline installer on specified path"""
    click.echo("Download offline media at {}".format(path))
    util.verify_create_dirs(path)
    apt_pkg_path = f"{path.rstrip('/')}/apt.tar.gz"
    voithos_pkg_path = f"{path.rstrip('/')}/voithos.tar.gz"
    if os.path.exists(apt_pkg_path) and not force:
        error(
            f"Warning: {apt_pkg_path} already exists: use --force to overwrite.",
            exit=False,
        )
    else:
        s3.download(path + "/apt.tar.gz", "voithos-files", "apt.tar.gz")
    if os.path.exists(voithos_pkg_path) and not force:
        error(
            f"Warning: {voithos_pkg_path} already exists: use --force to overwrite.",
            exit=False,
        )
    else:
        s3.download(path + "/voithos.tar.gz", "voithos-files", "voithos.tar.gz")
    util.pull_and_save_kolla_tag_images(kolla_tag, path, force)
    util.pull_and_save_bw_tag_images(bw_tag, path, force)
    util.pull_and_save_single_image("ceph-ansible", ceph_release, f"{path}/images/", force)


@click.command(name="upload-apt-packages-s3")
def create_and_upload_apt_tar():
    """ Create and upload apt tar file on S3"""
    util.create_and_upload_offline_apt_repo_tar_file()


@click.option("--voithos-branch", required=False, default="master", help="git checkout of voithos")
@click.command(name="upload-voithos-package-s3")
def create_and_upload_voithos_tar(voithos_branch):
    """ Package voithos along with its dependencies and upload to s3"""
    util.create_and_upload_offline_voithos_tar_file(voithos_branch)


@click.option("--name", required=True, help="Image name")
@click.option("--tag", required=True, help="Image tag")
@click.option("--path", required=True, help="Offline media path")
@click.option(
    "--force/--no-force",
    default=False,
    help="Use --force to overwrite files if they already exists",
)
@click.command(name="export-offline-image")
def export_offline_single_image(name, tag, path, force):
    """ Download single image at <path>/images/ """
    util.verify_create_dirs(path)
    util.pull_and_save_single_image(name, tag, path, force)


def get_util_group():
    """ Return the util group """

    @click.group(name="util")
    def util_group():
        """ Voithos utilities """

    util_group.add_command(get_qemu_img_group())
    util_group.add_command(export_offline_media)
    util_group.add_command(export_offline_single_image)
    util_group.add_command(create_and_upload_apt_tar)
    util_group.add_command(create_and_upload_voithos_tar)
    return util_group
