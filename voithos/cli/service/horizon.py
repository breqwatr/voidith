""" Manage the OpenStack Horizon container

    Due to Kolla-Ansible's hard-coding port 443 in HA-Proxy, we can't deploy Horizon through it
    while also deploying Arcus on the OpenStack control plane's VIP.
"""


import click
import voithos.lib.service.horizon as horizon


@click.option("--ip", "ip_address", default="0.0.0.0", help="[optional] bind IP address")
@click.option("--port", default="80", help="[optional] bind port (default 80)")
@click.option("--internal-vip", "internal_vip", required=True, help="Internal OpenStack VIP")
@click.option("--control-node-ip", "control_node_ip", required=True, help="IP of a control node running memcached")
@click.option(
    "--conf-dir", "conf_dir", default="/etc/kolla/horizon", help="[optional] Config dir override"
)
@click.option("--name", default="horizon", help="[optional] Container name override")
@click.option("--release", default="train", help="[optional] Docker image tag override")
@click.command()
def start(ip_address, port, internal_vip, control_node_ip, conf_dir, name, release):
    """ Launch the Horizon service """
    horizon.start(
        ip_address=ip_address,
        port=port,
        internal_vip=internal_vip,
        control_node_ip=control_node_ip,
        release=release,
        conf_dir=conf_dir,
        name=name)


def get_horizon_group():
    """ return the Horizon group function """

    @click.group(name="horizon")
    def horizon_group():
        """ Horizon service """

    horizon_group.add_command(start)
    return horizon_group
