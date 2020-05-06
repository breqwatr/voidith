""" Manage the local Docker registry service """


import click

import voithos.lib.service.registry as registry


@click.option("--ip", default="0.0.0.0", help="[optional] bind IP address")
@click.option("--port", default="5000", help="[optional] bind port")
@click.command()
def start(ip, port):
    """ Launch the local registry """
    registry.start(ip, port)


def get_registry_group():
    """ return the registry group function """

    @click.group(name="registry")
    def registry_group():
        """ Local Docker image registry """

    registry_group.add_command(start)
    return registry_group
