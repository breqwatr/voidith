""" Manage Arcus services """

import click

import voithos.cli.service.arcus.api as api
import voithos.cli.service.arcus.client as client
import voithos.cli.service.arcus.mgr as mgr


def get_arcus_group():
    """ return the arcus group function """

    @click.group(name="arcus")
    def arcus_group():
        """ Arcus services """

    arcus_group.add_command(api.get_api_group())
    arcus_group.add_command(client.get_client_group())
    arcus_group.add_command(mgr.get_mgr_group())
    return arcus_group
