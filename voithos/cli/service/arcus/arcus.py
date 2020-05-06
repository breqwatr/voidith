""" Manage Arcus services """

import click

import voithos.cli.service.arcus.api as api


def get_arcus_group():
    """ return the arcus group function """

    @click.group(name="arcus")
    def arcus_group():
        """ Arcus services """

    arcus_group.add_command(api.get_api_group())
    return arcus_group
