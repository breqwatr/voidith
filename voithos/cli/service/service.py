""" Command-group for Voithos Services """
import click

import voithos.cli.service.arcus.arcus as arcus
import voithos.cli.service.grafana as grafana
import voithos.cli.service.registry as registry
import voithos.cli.service.pxe as pxe


def get_service_group():
    """ Return the service click group """

    @click.group()
    def service():
        """ Manage Voithos services """

    service.add_command(arcus.get_arcus_group())
    service.add_command(grafana.get_grafana_group())
    service.add_command(pxe.get_pxe_group())
    service.add_command(registry.get_registry_group())
    return service
