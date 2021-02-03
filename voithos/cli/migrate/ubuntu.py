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
    return ubuntu
