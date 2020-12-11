""" Command-group: voithos migrate rhel """
import click

import voithos.lib.migrate.rhel as rhel


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

def get_rhel_group():
    """ Return the migrate click group """

    @click.group()
    def rhel():
        """ Operate on RHEL/CentOS VMs """

    rhel.add_command(add_virtio_drivers)
    rhel.add_command(get_boot_mode)
    return rhel
