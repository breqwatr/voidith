""" Operate the PXE  service """
from voithos.lib.docker import env_string
from voithos.lib.system import shell


def start(interface, dhcp_start, dhcp_end, release="stable"):
    """ Start the PXE service """
    image = f"breqwatr/pxe:{release}"
    env_vars = {
        "INTERFACE": interface,
        "DHCP_RANGE_START": dhcp_start,
        "DHCP_RANGE_END": dhcp_end
    }
    env_str = env_string(env_vars)
    shell(f"docker run -d --name pxe --network host {env_str} {image}")
