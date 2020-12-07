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


def get_registry_group():
    """ return the registry group function """

    @click.group(name="registry")
    def registry_group():
        """ Local Docker image registry """

    registry_group.add_command(start)
    registry_group.add_command(list_images)
    return registry_group
