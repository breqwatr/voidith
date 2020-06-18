""" Manage Arcus-Client service """

import click

import voithos.lib.aws.ecr as ecr
import voithos.lib.service.arcus.client as arcus_client
from voithos.lib.system import error
from voithos.constants import DEV_MODE


@click.option("--release", "-r", required=True, help="Version of Arcus API to run")
@click.command(name="pull")
def pull(release):
    """ Pull Arcus API from Breqwatr's private repository """
    image = f"breqwatr/arcus-client:{release}"
    ecr.pull(image)


@click.option("--release", "-r", required=True, help="Version of Arcus API to run")
@click.option("--api-ip", "api_ip", required=True, help="IP of Arcus API")
@click.option("--openstack-ip", "openstack_ip", required=True, help="IP/FQDN of OpenStack")
@click.option(
    "--glance-https/--glance-http", "glance_https", default=True, help="Does Glance use HTTPS?"
)
@click.option(
    "--arcus-https/--arcus-http", "arcus_https", default=False, help="Does Arcus Client use HTTPS?"
)
@click.option(
    "--cert-path", "cert_path", default=None, help="Path to Arcus Client's HTTPS certificate file"
)
@click.option(
    "--cert-key",
    "cert_key",
    default=None,
    help="Path to Arcus Client's HTTPS certificate private key file",
)
@click.option("--http-port", "http_port", default=80, help="HTTP listen port override")
@click.option("--https-port", "https_port", default=443, help="HTTPS listen port override")
@click.command(name="start")
def start(
    release,
    api_ip,
    openstack_ip,
    glance_https,
    arcus_https,
    cert_path,
    cert_key,
    http_port,
    https_port,
):
    """ Launch the arcus-client service """
    click.echo("starting arcus client")
    if arcus_https and (cert_path is None or cert_key is None):
        error("ERROR: Invalid HTPPS configuration for Arcus Client", exit=False)
        error("       Expected --cert-path and --cert-key when using --arcus-https", exit=True)
    arcus_client.start(
        release,
        api_ip,
        openstack_ip,
        glance_https,
        arcus_https=arcus_https,
        cert_path=cert_path,
        cert_key_path=cert_key,
        http_port=http_port,
        https_port=https_port,
    )


@click.command(name="rebuild")
def rebuild():
    if DEV_MODE is not True:
        error("ERROS: Dev mode is disabled")
        return
    arcus_client.rebuild()


def get_client_group():
    """ return the arcus group function """

    @click.group(name="client")
    def client_group():
        """ Arcus HTTP API service """

    client_group.add_command(pull)
    client_group.add_command(start)
    client_group.add_command(rebuild)
    return client_group
