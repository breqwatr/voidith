""" Command-group for Voithos Services """
import click

import voithos.cli.service.registry as registry


def get_services_group():
    """ Return the service click group """

    @click.group()
    def services():
        """ Manage Voithos services """

    services.add_command(registry.get_registry_group())
    return services
