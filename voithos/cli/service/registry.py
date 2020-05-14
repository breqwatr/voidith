""" Manage the local Docker registry service """


import click
import voithos.lib.service.registry as registry


@click.option("--ip", "ip_address", default="0.0.0.0", help="[optional] bind IP address")
@click.option("--port", default="5000", help="[optional] bind port")
@click.command()
def start(ip_address, port):
    """ Launch the local registry """
    registry.start(ip_address, port)


@click.argument("registry_url")
@click.command(name="list-images")
def list_images(registry_url):
    """ List the images in a registry """
    registry.list_images(registry_url)


def get_registry_group():
    """ return the registry group function """

    @click.group(name="registry")
    def registry_group():
        """ Local Docker image registry """

    registry_group.add_command(start)
    registry_group.add_command(list_images)
    return registry_group
