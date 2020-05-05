""" Command-group for Voidith Services """
import click

import voidith.cli.service.registry as registry


def get_services_group():
    """ Return the service click group """

    @click.group()
    def services():
        """ Manage Voidith services """

    services.add_command(registry.get_registry_group())
    return services
