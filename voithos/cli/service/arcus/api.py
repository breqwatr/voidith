""" Manage Arcus-API service """

import click

import voithos.lib.aws.ecr as ecr
import voithos.lib.service.arcus.api as arcus_api


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
    "--ceph/--no-ceph", required=True, default=False, help="use --ceph to enable Ceph features"
)
@click.option("--https/--http", default=True, required=True, help="Use --http to disable HTTPS")
@click.option("--port", default=1234, help="Override the listen port")
@click.command(name="start")
def start(release, openstack_fqdn, rabbit_pass, rabbit_ip, sql_ip, sql_password, ceph, https, port):
    """ Launch the arcus-api service """
    click.echo("starting arcus api")
    arcus_api.start(
        release=release,
        fqdn=openstack_fqdn,
        rabbit_pass=rabbit_pass,
        rabbit_ips_list=rabbit_ip,
        sql_ip=sql_ip,
        sql_password=sql_password,
        ceph_enabled=ceph,
        https=https,
        port=port,
    )


def get_api_group():
    """ return the arcus group function """

    @click.group(name="api")
    def api_group():
        """ Arcus HTTP API service """

    api_group.add_command(pull)
    api_group.add_command(start)
    api_group.add_command(database_init)
    return api_group


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
