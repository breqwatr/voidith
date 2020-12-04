""" Voithos Utilities """

import click
import voithos.lib.util.util as util
from voithos.cli.util.qemu_img import get_qemu_img_group


@click.option('--kolla-tag', required=True, help='Kolla images tag')
@click.option('--bw-tag', required=True, help='Breqwatr images tag')
@click.option('--ceph-release', required=False, default=None, help='Ceph version')
@click.option('--force/--no-force', default=False,
              help='Use --force to overwrite files if they already exists')
@click.option('--path', required=True, help='Download path')
@click.command(name='export-offline-media')
def export_offline_media(kolla_tag, bw_tag, ceph_release, force, path):
    """ Download offline installer on specified path"""
    click.echo("Download offline media at {}".format(path))
    util.verify_create_dirs(path)
    util.pull_and_save_kolla_tag_images(kolla_tag, path, force)
    util.pull_and_save_bw_tag_images(bw_tag, path, force)
    util.pull_and_save_single_image("ceph-ansible", ceph_release, path, force)

@click.option('--name', required=True, help='Image name')
@click.option('--tag', required=True, help='Image tag')
@click.option('--path', required=True, help='Download path')
@click.option('--force/--no-force', default=False,
              help='Use --force to overwrite files if they already exists')
@click.command(name='export-offline-image')
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
    return util_group
