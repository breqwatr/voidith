""" Command-group for Voithos Services """
import click

import voithos.cli.service.arcus.arcus as arcus
import voithos.cli.service.registry as registry


def get_service_group():
    """ Return the service click group """

    @click.group()
    def service():
        """ Manage Voithos services """

    service.add_command(registry.get_registry_group())
    service.add_command(arcus.get_arcus_group())
    return service
