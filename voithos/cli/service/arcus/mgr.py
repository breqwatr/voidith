""" Manage Arcus-Mgr service """

import click

import voithos.lib.aws.ecr as ecr
import voithos.lib.service.arcus.mgr as arcus_mgr


@click.option("--release", "-r", required=True, help="Version of Arcus API to run")
@click.command(name="pull")
def pull(release):
    """ Pull Arcus-Mgr from Breqwatr's private repository """
    image = f"breqwatr/arcus-mgr:{release}"
    ecr.pull(image)


@click.option("--release", "-r", required=True, help="Version of Arcus API to run")
@click.option("--openstack-vip", "openstack_vip", required=True, help="VIP for OpenStack")
@click.option("--sql-pass", "sql_pass", required=True, help="SQL password for arcus user")
@click.option("--sql-ip", "sql_ip", required=True, help="IP Address of SQL")
@click.option("--rabbit-pass", required=True, help="RabbitMQ password")
@click.option(
    "--ceph/--no-ceph", required=True, default=False, help="use --ceph to enable Ceph features"
)
@click.option(
    "--rabbit-ip",
    "rabbit_ips_list",
    required=True,
    multiple=True,
    help="IP(s) of RabbitMQ service. Repeat for each IP.",
)
@click.command(name="start")
def start(release, openstack_vip, sql_pass, sql_ip, rabbit_ips_list, rabbit_pass, ceph):
    """ Launch the arcus-mgr service """
    click.echo("starting arcus manager")
    enable_ceph = "true" if ceph else "false"
    arcus_mgr.start(
        release, openstack_vip, sql_pass, sql_ip, rabbit_ips_list, rabbit_pass, enable_ceph
    )


def get_mgr_group():
    """ return the arcus mgr group function """

    @click.group(name="mgr")
    def mgr_group():
        """ Arcus Manager service """

    mgr_group.add_command(pull)
    mgr_group.add_command(start)
    return mgr_group
