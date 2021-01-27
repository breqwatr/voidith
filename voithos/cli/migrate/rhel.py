""" Command-group: voithos migrate rhel """
import click

from voithos.lib.migrate.rhel import RhelWorker
from voithos.lib.system import error


@click.argument("devices", nargs=-1)
@click.command(name="get-boot-mode")
def get_boot_mode(devices):
    """ Print the boot mode (UEFI or BIOS) of a device """
    print(RhelWorker(devices).boot_mode)


@click.argument("devices", nargs=-1)
@click.command(name="get-mount-cmds")
def get_mount_cmds(devices):
    """ Print mount and unmount commands """
    rhel_worker = RhelWorker(devices)
    print(f"# mount to {rhel_worker.ROOT_MOUNT}:")
    print("#")
    for mount_opts in rhel_worker.get_ordered_mount_opts():
        bind = "--bind" if mount_opts["bind"] else ""
        if not mount_opts["bind"]:
            print(f"mkdir -p {mount_opts['mnt_to']}")
        print(f"mount {mount_opts['mnt_from']} {mount_opts['mnt_to']} {bind}")
    print("#")
    print(f"# to chroot into the guest system:  chroot {rhel_worker.ROOT_MOUNT} /bin/bash")
    print("#")
    print("# to unmount:")
    for mount_opts in rhel_worker.get_ordered_mount_opts(reverse=True):
        print(f"umount {mount_opts['mnt_to']}")


@click.argument("devices", nargs=-1)
@click.command()
def mount(devices):
    """ Mount all the devices partitions from the root volume's fstab """
    RhelWorker(devices).mount_volumes(print_progress=True)


@click.option("--force/--no-force", "force", default=False, help="Skip the prompts")
@click.command()
def unmount(force):
    """ Unmount all the devices partitions from the root volume's fstab """
    RhelWorker().unmount_volumes(print_progress=True)


@click.option("--force/--no-force", "force", default=False, help="Use force to reinstall")
@click.command(name="add-virtio-drivers")
def add_virtio_drivers(force):
    """ Add VirtIO drivers to mounted volume/device """
    RhelWorker().add_virtio_drivers(force)


@click.command(name="vmware-tools")
def uninstall_vmware_tools():
    """ Uninstall VMware Tools """
    RhelWorker().uninstall("vm-tools", like=True)


@click.command(name="cloud-init")
def uninstall_cloud_init():
    """ Uninstall Cloud-Init """
    RhelWorker().uninstall("cloud-init", like=True)


@click.argument("package")
@click.command(name="package")
def uninstall_package(package):
    """ Uninstall the given package """
    RhelWorker().uninstall(package, like=True)


@click.argument("devices", nargs=-1)
@click.command(name="repair-partitions")
def repair_partitions(devices):
    """ Repair the partitions on this device """
    RhelWorker(devices).repair_partitions()


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
@click.command(name="set-interface")
def set_interface(dhcp, mac, ip_addr, name, prefix, gateway, dns, domain):
    """ Create udev rules to define NICs """
    if dhcp:
        if ip_addr is not None or prefix is not None or gateway is not None:
            error("ERROR: --ip-addr, --prefix, and --gateway require --static", exit=True)
    else:
        if ip_addr is None or prefix is None:
            error("ERROR: --ip-addr and --prefix are required with --static", exit=True)
    RhelWorker().set_udev_interface(
        interface_name=name,
        is_dhcp=dhcp,
        mac_addr=mac,
        prefix=prefix,
        gateway=gateway,
        dns=dns,
        domain=domain,
        ip_addr=ip_addr,
    )


@click.argument("devices", nargs=-1)
@click.command(name="get-partition-names")
def get_partition_names(devices):
    """ Print the paths of the partitions on a device """
    worker = RhelWorker(devices)
    print(f"Root Partition: {worker.root_volume}")
    if worker.boot_partition_is_on_root_volume:
        printf("/boot is on the root partition, not its own volume")
    else:
        print(f"Boot Partition: {worker.boot_volume}")


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
    uninstall.add_command(uninstall_package)
    rhel.add_command(uninstall)
    rhel.add_command(set_interface)
    rhel.add_command(get_partition_names)
    rhel.add_command(get_mount_cmds)
    rhel.add_command(mount)
    rhel.add_command(unmount)
    return rhel
