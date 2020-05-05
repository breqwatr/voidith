""" Entrypoint for voithos CLI """

import sys

import click

import voithos.cli.ceph as ceph
import voithos.cli.openstack as openstack
import voithos.cli.services as services
import voithos.constants as constants
from voithos.lib.system import error


# Requires python 3
if sys.version_info[0] != 3:
    error("ERROR: Python3 required", exit=True, code=42)


@click.command()
def version():
    """ Show the current version """
    click.echo(constants.VOITHOS_VERSION)


def get_entrypoint():
    """ Return the entrypoint click group """

    @click.group()
    def entrypoint():
        """ Entrypoint for Click """

    entrypoint.add_command(version)
    entrypoint.add_command(ceph.get_ceph_group())
    entrypoint.add_command(openstack.get_openstack_group())
    entrypoint.add_command(services.get_services_group())
    return entrypoint


def main():
    """ Entrypoint defined in setup.py for voithos command """
    try:
        entrypoint = get_entrypoint()
        entrypoint()
    except KeyboardInterrupt:
        # Handle ctrl+C without dumping a stack-trace
        error("CTRL+C detected, exiting", exit=True, code=2)
