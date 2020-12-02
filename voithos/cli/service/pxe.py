""" Manage the PXE  service """
import click

import voithos.lib.aws.ecr as ecr
import voithos.lib.service.pxe as pxe


@click.option("--interface", required=True, help="Network interface to bind to")
@click.option("--dhcp-start", "dhcp_start", required=True, help="(IP Address)")
@click.option("--dhcp-end", "dhcp_end", required=True, help="(IP Address)")
@click.option("--release", "-r", required=False, default="stable", help="Docker image tag")
@click.command()
def start(interface, dhcp_start, dhcp_end, release):
    """ Launch the local registry """
    pxe.start(interface, dhcp_start, dhcp_end, release=release)


@click.option("--release", "-r", required=True, help="Version of Breqwatr pxe to run")
@click.command(name="pull")
def pull(release):
    """ Pull PXE image from Breqwatr's private repository """
    image = f"breqwatr/pxe:{release}"
    ecr.pull(image)


def get_pxe_group():
    """ return the registry group function """

    @click.group(name="pxe")
    def pxe_group():
        """ PXE server service """

    pxe_group.add_command(start)
    pxe_group.add_command(pull)
    return pxe_group
