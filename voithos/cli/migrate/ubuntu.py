""" Command-group: voithos migrate ubuntu """
import click

# from voithos.lib.migrate.ubuntu import UbuntuWorker
from voithos.lib.migrate.ubuntu import UbuntuWorker
from voithos.lib.system import error


@click.argument("devices", nargs=-1)
@click.command(name="get-boot-mode")
def get_boot_mode(devices):
    """ Print the boot mode (UEFI or BIOS) of a device """
    print(UbuntuWorker(devices).boot_mode)


@click.argument("devices", nargs=-1)
@click.command()
def mount(devices):
    """ Mount all the devices partitions from the root volume's fstab """
    UbuntuWorker(devices).mount_volumes(print_progress=True)


@click.command()
def unmount():
    """ Unmount all the devices partitions from the root volume's fstab """
    UbuntuWorker().unmount_volumes(print_progress=True)


@click.argument("devices", nargs=-1)
@click.command(name="repair-partitions")
def repair_partitions(devices):
    """ Repair the partitions on this device """
    UbuntuWorker(devices).repair_partitions()


@click.group()
def uninstall():
    """ Uninstall packages """


@click.command(name="vmware-tools")
def uninstall_vmware_tools():
    """ Uninstall VMware Tools """
    UbuntuWorker().uninstall("vm-tools", like=True)


@click.command(name="cloud-init")
def uninstall_cloud_init():
    """ Uninstall Cloud-Init """
    UbuntuWorker().uninstall("cloud-init", like=True)


@click.option("--dhcp/--static", default=True, help="DHCP or Static IP (default DHCP)")
@click.option("--mac", "-m", required=True, help="Interface MAC address")
@click.option("--ip-addr", "-i", help="IP Address (requires --static)")
@click.option("--name", "-n", required=True, help="Interface name, ex: ens0, ens1, ens2")
@click.option("--prefix", "-p", help="Subnet prefix (requires --static), ex: 24")
@click.option("--gateway", "-g", default=None, help="Optional default gateway (requires --static)")
@click.option("--dns", "-d", multiple=True, default=None, help="Repeatable Optional DNS values")
@click.option("--domain", default=None, help="Optional search domain")
@click.command(name="set-interface")
def set_interface(dhcp, mac, ip_addr, name, prefix, gateway, dns, domain):
    """ Create udev rules to define NICs """
    if dhcp:
        if ip_addr is not None or prefix is not None or gateway is not None:
            error("ERROR: --ip-addr, --prefix, and --gateway require --static", exit=True)
    else:
        if ip_addr is None or prefix is None:
            error("ERROR: --ip-addr and --prefix are required with --static", exit=True)
    worker = UbuntuWorker()
    # worker.set_udev_interface_mapping(interface_name=name, mac_addr=mac)
    worker.set_interface(
        interface_name=name,
        is_dhcp=dhcp,
        mac_addr=mac,
        prefix=prefix,
        gateway=gateway,
        dns=dns,
        domain=domain,
        ip_addr=ip_addr,
    )


def get_ubuntu_group():
    """ Return the migrate click group """

    @click.group()
    def ubuntu():
        """ Operate on Ubuntu VMs """

    ubuntu.add_command(get_boot_mode)
    ubuntu.add_command(mount)
    ubuntu.add_command(unmount)
    ubuntu.add_command(repair_partitions)
    uninstall.add_command(uninstall_vmware_tools)
    uninstall.add_command(uninstall_cloud_init)
    ubuntu.add_command(uninstall)
    ubuntu.add_command(set_interface)
    return ubuntu
