""" Command-group: voithos migrate rhel """
import click

import voithos.lib.migrate.rhel as rhel
from voithos.lib.migrate.rhel import RhelWorker
from voithos.lib.system import error


def require_args(argument, qty=1):
    """ Exit if the given length of an nargs argument is < qty """
    num_args = len(argument)
    if num_args < qty:
        error(f"ERROR: arguments received: {num_args} - arguments required: >= {qty}", exit=True)


@click.argument("devices", nargs=-1)
@click.command(name="get-boot-mode")
def get_boot_mode(devices):
    """ Print the boot mode (UEFI or BIOS) of a device """
    require_args(devices)
    print(RhelWorker(devices).boot_mode)


@click.argument("devices", nargs=-1)
@click.command(name="get-mount-cmds")
def get_mount_cmds(devices):
    """ Print mount and unmount commands """
    require_args(devices)
    rhel_worker = RhelWorker(devices)
    print(f"# mount to {rhel_worker.ROOT_MOUNT}:")
    print("#")
    for mount_opts in rhel_worker.get_ordered_mount_opts():
        bind = "--bind" if mount_opts["bind"] else ""
        if not mount_opts["bind"]:
            print(f"mkdir -p {mount_opts['mnt_to']}")
        print(f"mount {mount_opts['mnt_from']} {mount_opts['mnt_to']} {bind}")
    print("#")
    print(f"# to chroot into the guest system:  chroot {rhel.ROOT_MOUNT} /bin/bash")
    print("#")
    print("# to unmount:")
    for mount_opts in rhel_worker.get_ordered_mount_opts(reverse=True):
        print(f"umount {mount_opts['mnt_to']}")


@click.argument("devices", nargs=-1)
@click.command()
def mount(devices):
    """ Mount all the devices partitions from the root volume's fstab """
    require_args(devices)
    RhelWorker(devices).mount_volumes(print_progress=True)


@click.argument("devices", nargs=-1)
@click.option("--force/--no-force", "force", default=False, help="Skip the prompts")
@click.command()
def unmount(devices, force):
    """ Unount all the devices partitions from the root volume's fstab """
    require_args(devices)
    RhelWorker(devices).unmount_volumes(prompt=(not force), print_progress=True)


@click.argument("devices", nargs=-1)
@click.command(name="add-virtio-drivers")
def add_virtio_drivers(devices):
    """ Add VirtIO drivers to mounted volume/device """
    require_args(devices)
    RhelWorker.add_virtio_drivers()

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
        ip_addr=ip_addr,
    )


@click.argument("devices", nargs=-1)
@click.command(name="get-partition-names")
def get_partition_names(devices):
    """ Print the paths of the partitions on a device """
    rhel_worker = RhelWorker(devices)
    print(f"Boot Partition: {rhel_worker.boot_volume}")
    if rhel_worker.boot_partition_is_on_root_volume:
        printf("/boot is on the root partition, not its own volume")
    else:
        print(f"Root Partition: {rhel.root_volume}")


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
    rhel.add_command(get_partition_names)
    rhel.add_command(get_mount_cmds)
    rhel.add_command(mount)
    rhel.add_command(unmount)
    return rhel
