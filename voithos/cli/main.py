""" Entrypoint for voithos CLI """

import sys

import click
import urllib3

import voithos.cli.ceph as ceph
import voithos.cli.config as config
import voithos.cli.openstack as openstack
import voithos.cli.service.service as service
import voithos.cli.util.util as util
import voithos.cli.vmware as vmware
import voithos.constants as constants
from voithos.lib.system import error


# Globally disable https warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
    entrypoint.add_command(config.get_config_group())
    entrypoint.add_command(openstack.get_openstack_group())
    entrypoint.add_command(service.get_service_group())
    entrypoint.add_command(util.get_util_group())
    entrypoint.add_command(vmware.get_vmware_group())
    return entrypoint


def main():
    """ Entrypoint defined in setup.py for voithos command """
    try:
        entrypoint = get_entrypoint()
        entrypoint()
    except KeyboardInterrupt:
        # Handle ctrl+C without dumping a stack-trace
        error("CTRL+C detected, exiting", exit=True, code=2)
