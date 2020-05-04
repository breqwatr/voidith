""" Entrypoint for voidith CLI """

import sys

import click

import voidith.cli.ceph as ceph
import voidith.cli.services as services
import voidith.constants as constants

# Requires python 3
if sys.version_info[0] != 3:
    sys.stderr.write("ERROR: Python 3 required \n")
    sys.exit(42)


@click.command()
def version():
    """ Show the current version """
    click.echo(constants.VOIDITH_VERSION)


def get_entrypoint():
    """ Return the entrypoint click group """

    @click.group()
    def entrypoint():
        """ Entrypoint for Click """

    entrypoint.add_command(version)
    entrypoint.add_command(ceph.get_ceph_group())
    entrypoint.add_command(services.get_services_group())
    return entrypoint


def main():
    """ Entrypoint defined in setup.py for voidith command """
    try:
        entrypoint = get_entrypoint()
        entrypoint()
    except KeyboardInterrupt:
        # Handle ctrl+C without dumping a stack-trace
        sys.exit(100)
