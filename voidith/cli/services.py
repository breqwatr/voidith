""" Command-group for Voidith Services """
import click


def get_services_group():
    """ Return the service click group """

    @click.group()
    def services():
        """ Manage Voidith services """

    return services
