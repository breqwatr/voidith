""" Command-group: voithos migrate rhel """
import click

import voithos.lib.migrate.rhel as rhel
from voithos.lib.system import error


@click.argument("device")
@click.command(name="add-virtio-drivers")
def add_virtio_drivers(device):
    """ Add VirtIO drivers to mounted volume/device """
    print(f"Adding VirtIO drivers to {device}")
    rhel.add_virtio_drivers(device)


@click.argument("device")
@click.command(name="get-boot-mode")
def get_boot_mode(device):
    """ Print the boot mode (UEFI or BIOS) of a device """
    boot_mode = rhel.get_boot_mode(device)
    print(boot_mode)


@click.argument("device")
@click.command(name="repair-partitions")
def repair_partitions(device):
    """ Repair the partitions on this device """
    rhel.repair_partitions(device)


@click.argument("device")
@click.command(name="vmware-tools")
def uninstall_vmware_tools(device):
    """ Uninstall VMware Tools """
    rhel.uninstall(device, "vm-tools", like=True)


@click.argument("device")
@click.command(name="cloud-init")
def uninstall_cloud_init(device):
    """ Uninstall Cloud-Init """
    rhel.uninstall(device, "cloud-init", like=True)


@click.group()
def uninstall():
    """ Uninstall packages """


@click.option("--dhcp/--static", default=True, help="DHCP or Static IP (default DHCP)")
@click.option("--mac", "-m", required=True, help="Interface MAC address")
@click.option("--ip-addr", "-i", help="IP Address (requires --static)")
@click.option("--name", "-n", required=True, help="Interface name, ex: ens0, ens1, ens2")
@click.option("--prefix", "-p", help="Subnet prefix (requires --static), ex: 24")
@click.option("--gateway", "-g", default=None, help="Optional default gateway (requires --static)")
@click.option("--dns", "-d", multiple=True, default=None, help="Repeatable Optional DNS values")
@click.option("--domain", default=None, help="Optional search domain")
@click.argument("device")
@click.command(name="set-interface")
def set_interface(device, dhcp, mac, ip_addr, name, prefix, gateway, dns, domain):
    """ Create udev rules to define NICs """
    if dhcp:
        if ip_addr is not None or prefix is not None or gateway is not None:
            error("ERROR: --ip-addr, --prefix, and --gateway require --static", exit=True)
    else:
        if ip_addr is None or prefix is None:
            error("ERROR: --ip-addr and --prefix are required with --static", exit=True)
    rhel.set_udev_interface(
        device=device,
        interface_name=name,
        is_dhcp=dhcp,
        mac_addr=mac,
        prefix=prefix,
        gateway=gateway,
        dns=dns,
        domain=domain,
        ip_addr=ip_addr
    )


def get_rhel_group():
    """ Return the migrate click group """

    @click.group()
    def rhel():
        """ Operate on RHEL/CentOS VMs """

    rhel.add_command(add_virtio_drivers)
    rhel.add_command(get_boot_mode)
    rhel.add_command(repair_partitions)
    uninstall.add_command(uninstall_vmware_tools)
    uninstall.add_command(uninstall_cloud_init)
    rhel.add_command(uninstall)
    rhel.add_command(set_interface)
    return rhel
