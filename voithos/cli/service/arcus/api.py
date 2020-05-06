""" Manage Arcus-API service """

import click


import voithos.lib.service.arcus as arcus


@click.command(name="pull")
def pull():
    """ Pull Arcus API from Breqwatr's private repository """
    arcus.pull("api")


@click.command(name="start")
def start():
    """ Launch the arcus-api service """


def get_api_group():
    """ return the arcus group function """

    @click.group(name="api")
    def api_group():
        """ Arcus HTTP API service """

    api_group.add_command(pull)
    api_group.add_command(start)
    return api_group
