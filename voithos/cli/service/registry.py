""" Manage the local Docker registry service """


import click
import voithos.lib.service.registry as registry
from voithos.lib.system import error


@click.option("--ip", "ip_address", default="0.0.0.0", help="[optional] bind IP address")
@click.option("--port", default="5000", help="[optional] bind port")
@click.option("--path", "--offline-path", required=False, help="registry image path (for offline install only)")
@click.command()
def start(ip_address, port, path):
    """ Launch the local registry """
    if path:
       registry.offline_start(ip_address, port, path)
    else:
        registry.start(ip_address, port)

@click.argument("registry_url")
@click.command(name="list-images")
def list_images(registry_url):
    """ List the images in a registry """
    if not registry_url.startswith('http'):
        error("ERROR: Registry URL must start with protocol (http/https)", exit=True)
    registry.list_images(registry_url)

@click.option('--kolla-tag', required=True, help='Kolla images tag')
@click.option('--bw-tag', required=True, help='Breqwatr images tag')
@click.option('--ceph-release', required=False, default=None, help='Ceph version')
@click.option("--path", "--offline-path", required=True, help="registry image path (for offline install only)")
@click.option("--keep/--delete-local", default=True, help="Keep or delete local images")
@click.argument("local_registry")
@click.command(name="sync-offline-images-to-registry")
def sync_local_registry_offline(kolla_tag, bw_tag, ceph_release, path, keep, local_registry):
    """ Sync registry with offline images"""
    if local_registry.startswith("http"):
        error("Registry must not start with http/https.", exit=False)
        error("If push failed, ensure /etc/docker/daemon.json is correct", exit=True)
    registry.sync_offline_images(kolla_tag, bw_tag, ceph_release, path, keep, local_registry)

@click.option('--name', required=True, help='Image name')
@click.option('--tag', required=True, help='Image tag')
@click.option("--path", "--offline-path", required=True, help="registry image path (for offline install only)")
@click.option("--keep/--delete-local", default=True, help="Keep or delete local images")
@click.argument("local_registry")
@click.command(name="sync-offline-image-to-registry")
def sync_image_to_registry_offline(name, tag, path, keep, local_registry):
    """ Sync registry with offline image"""
    if local_registry.startswith("http"):
        error("Registry must not start with http/https.", exit=False)
        error("If push failed, ensure /etc/docker/daemon.json is correct", exit=True)
    registry.sync_offline_single_image(name, tag, path, keep, local_registry)

def get_registry_group():
    """ return the registry group function """

    @click.group(name="registry")
    def registry_group():
        """ Local Docker image registry """

    registry_group.add_command(start)
    registry_group.add_command(list_images)
    registry_group.add_command(sync_local_registry_offline)
    registry_group.add_command(sync_image_to_registry_offline)
    return registry_group
