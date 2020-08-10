""" Manage the OpenStack Horizon container

    Due to Kolla-Ansible's hard-coding port 443 in HA-Proxy, we can't deploy Horizon through it
    while also deploying Arcus on the OpenStack control plane's VIP.
"""


import click
import voithos.lib.service.horizon as horizon


@click.option("--ip", "ip_address", default="0.0.0.0", help="[optional] bind IP address")
@click.option("--port", default="80", help="[optional] bind port (default 80)")
@click.option("--openstack-fqdn", "openstack_fqdn", required=True, help="OpenStack VIP")
@click.option(
    "--keystone-url",
    "keystone_url",
    required=True,
    help="Full keystone URL. Example: http://preview.breqwatr.com:5000/v3",
)
@click.command()
def start(ip_address, port, openstack_fqdn, keystone_url):
    """ Launch the Horizon service """
    horizon.start(ip_address, port, openstack_fqdn, keystone_url)


def get_horizon_group():
    """ return the Horizon group function """

    @click.group(name="horizon")
    def horizon_group():
        """ Horizon service """

    horizon_group.add_command(start)
    return horizon_group
