""" Manage Arcus-API service """

import click

import voithos.lib.aws.ecr as ecr
import voithos.lib.service.arcus.api as arcus_api
import voithos.lib.service.arcus.common as arcus_common
import voithos.cli.service.arcus.integrations as integrations


@click.option("--release", "-r", required=True, help="Version of Arcus API to run")
@click.command(name="pull")
def pull(release):
    """ Pull Arcus API from Breqwatr's private repository """
    image = f"breqwatr/arcus-api:{release}"
    ecr.pull(image)


@click.option("--release", "-r", required=True, help="Version of Arcus API to run")
@click.option("--openstack-fqdn", required=True, help="fqdn/VIP of openstack")
@click.option("--rabbit-pass", required=True, help="RabbitMQ password")
@click.option(
    "--rabbit-ip",
    required=True,
    multiple=True,
    help="IP(s) of RabbitMQ service. Repeat for each IP.",
)
@click.option("--sql-ip", required=True, help="IP/VIP of SQL service")
@click.option("--sql-password", required=True, help="password for SQL service")
@click.option(
    "--https/--http", default=True, required=True, help="Does OpenStack use HTTPS or HTTP"
)
@click.option("--port", default=1234, help="Override the listen port")
@click.option("--secret", required=True, help="Secret key / password for integrations")
@click.command(name="start")
def start(
    release,
    openstack_fqdn,
    rabbit_pass,
    rabbit_ip,
    sql_ip,
    sql_password,
    https,
    port,
    secret,
):
    """ Launch the arcus-api service """
    click.echo("starting arcus api")
    arcus_api.start(
        release=release,
        fqdn=openstack_fqdn,
        rabbit_pass=rabbit_pass,
        rabbit_ips_list=rabbit_ip,
        sql_ip=sql_ip,
        sql_password=sql_password,
        https=https,
        port=port,
        secret=secret,
    )


@click.option("--release", "-r", required=True, help="Version of Arcus API to run")
@click.command(name="update")
def update(release,):
    """ Update arcus api """
    click.echo("Updating arcus api to version: {}".format(release))
    arcus_common.update(release, "api")

@click.option("--host", required=True, help="MariaDB IP or FQDN")
@click.option("--admin-user", required=True, help="Admin user for creating the new DB")
@click.option("--admin-pass", required=True, help="Amin user password")
@click.option("--arcus-pass", required=True, help='New "arcus" DB user password')
@click.command(name="database-init")
def database_init(host, admin_user, admin_pass, arcus_pass):
    """ Initialize the Arcus database """
    click.echo("Initializing Arcus database")
    res = arcus_api.init_database(
        host=host, admin_user=admin_user, admin_passwd=admin_pass, arcus_passwd=arcus_pass
    )
    for key in res:
        click.echo(f"{key} {res[key]}")


@click.option("--auth-url", "-o", "auth_url", required=True, help="OpenStack Auth URL")
@click.option("--username", "-u", required=True, help="OpenStack SA username")
@click.option("--password", "-p", required=True, help="Openstack SA password")
@click.option("--api-url", "-a", "api_url", required=True, help="Arcus API address (with port)")
@click.command(name="set-service-account")
def set_service_account(auth_url, username, password, api_url):
    """ Set/create the openstack service account for Arcus API """
    if not api_url.startswith("http"):
        click.echo("Arcus API URL must start with protocol (http/https)")
        return
    arcus_api.set_service_account(auth_url, username, password, api_url)


def get_api_group():
    """ return the arcus group function """

    @click.group(name="api")
    def api_group():
        """ Arcus HTTP API service """

    api_group.add_command(pull)
    api_group.add_command(start)
    api_group.add_command(update)
    api_group.add_command(database_init)
    api_group.add_command(set_service_account)
    api_group.add_command(integrations.get_integrations_group())
    return api_group
