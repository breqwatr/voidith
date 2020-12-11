""" Library for RHEL migration operations """
import psutil
from pathlib import Path

from voithos.lib.system import (
    error,
    run,
    assert_block_device_exists,
    mount,
    unmount,
    get_file_contents,
)


# Mountpoints for volume work to be done
MOUNT_BASE = "/convert"
EFI_MOUNT = f"{MOUNT_BASE}/efi"
BOOT_MOUNT = f"{MOUNT_BASE}/boot"
ROOT_MOUNT = f"{MOUNT_BASE}/root"


class FailedMount(Exception):
    """ A mount operation has failed """


def unmount_partitions():
    """ Unmount all the worker partitions to ensure a clean setup """
    unmount(EFI_MOUNT, prompt=True)
    unmount(BOOT_MOUNT, prompt=True)
    unmount(ROOT_MOUNT, prompt=True)


def get_boot_mode(device):
    """ Return either "UEFI" or "BIOS" - Determine how this device boots """
    fdisk = run(f"fdisk -l {device}")
    disk_type_line = next((line for line in fdisk if "Disklabel type" in line), None)
    if disk_type_line is None:
        error(f"Error: Failed to determine boot mode of {device}", exit=True)
    disk_type = disk_type_line.split(" ")[-1]
    return "UEFI" if (disk_type == "gpt") else "BIOS"


def get_bios_boot_partition(device):
    """ Return path of  boot partition in a BIOS style device """
    fdisk = run(f"fdisk -l {device}")
    # It's always the first one, but get the one with * in the boot column just in case
    boot_line = next(line for line in fdisk if "*" in line and line.startswith(device))
    return boot_line.split(" ")[0]


def get_uefi_boot_partition(device):
    """ Return path (str) of boot partition in a UEFI style device
        There's a chance it won't find it. If so, return None.
    """
    try:
        mount(efi_partition, EFI_MOUNT)
        grub_path = f"{EFI_MOUNT}/EFI/redhat/grub.cfg"
        grub_contents = get_file_contents(grub_path, required=True)
        efi_partition = get_efi_partition(device)
        for partition in get_partitions():
            if partition == efi_partition:
                continue
            uuid = get_partition_uuid(partition)
            if uuid in grub_contents:
                return partition
    finally:
        unmount(EFI_MOUNT)
    return None


def get_partitions(device):
    """ Return a list of partitions on a device """
    fdisk = run(f"fdisk -l {device}")
    partitions = []
    partition_lines = (line for line in fdisk if line.startswith(device))
    for partition_line in partition_lines:
        partitions.append(partition_line.split(" ")[0])
    return partitions


def get_efi_partition(device):
    """ Find which partition is the EFI partition """
    fdisk = run(f"fdisk -l {device}")
    efi_line = next(line for line in fdisk if line.startswith(device) and "EFI" in line)
    return efi_line.split(" ")[0]


def get_partition_uuid(partition):
    """ Return the UUID of a partition """
    blkid = execute(f"blkid {partition}")
    return blkid[0].split(" ")[1].replace("UUID=", "").replace('"', "")


def get_pvs():
    """ Return a list of LVM physical volumes """
    pvs = []
    pv_lines = run(f"pvdisplay")
    pv_name_lines = [ line for line in pv_lines if "PV Name" in line ]
    for pv_name_line in pv_name_lines:
        name = pv_name_line.strip().split(" ")[-1]
        pvs.append(name)
    return pvs


def get_logical_volumes(partition):
    """ Return a list of dicts with logical volumes names and device mapper paths """
    lvs = []
    if partition not in get_pvs():
        return lvs
    pv_lines = run(f"pvdisplay -m {partition}", exit_on_error=True)
    lv_lines = [ line for line in pv_lines if "Logical volume" in line ]
    for lv_line in lv_lines:
        lv_name = lv_line.strip().split("\t")[1]
        lv_split = lv_name.split("/")
        dm_path = f"/dev/mapper/{lv_split[-2]}-{lv_split[-1]}"
        lvs.append({"lv": lv_name, "dm": dm_path})
    return lvs


def get_fs_type(partition):
    """ Return the filesystem type of a partition """
    blkid_lines = run(f"blkid {partition}")
    line = next(line for line in blkid_lines if partition in line)
    elem = next(elem for elem in line.split(" ") if "TYPE=" in elem)
    # example: convert 'TYPE="ext4"' to ext4
    fs_type = elem.replace('"',"").split("=")[1]
    return fs_type


def is_root_partition(partition):
    """ Check if a given partition is the root partition, return Boolean """
    fs_type = get_fs_type(partition)
    if fs_type == "LVM2_member" or fs_type == "swap":
        return False
    is_root = False
    try:
        mount(partition, ROOT_MOUNT)
        is_root = Path(f"{ROOT_MOUNT}/etc/fstab").is_file()
    finally:
        unmount(ROOT_MOUNT)
    return is_root


def get_root_partition(device):
    """ Find the root partition of a device """
    for partition in get_partitions(device):
        fs_type = get_fs_type(partition)
        if fs_type == "LVM2_member":
            logical_volumes = get_logical_volumes(partition)
            for volume in logical_volumes:
                if is_root_partition(volume["dm"]):
                    return volume["lv"]
            continue
        else:
            if is_root_partition(partition):
                return partition


def add_virtio_drivers(device):
    """  Add VirtIO drivers to mounted volume/device """
    assert_block_device_exists(device)
    unmount_partitions()
    boot_mode = get_boot_mode(device)
    print(f"Boot Style: {boot_mode}")
    if boot_mode == "BIOS":
        boot_partition = get_bios_boot_partition(device)
    else:
        boot_partition = get_uefi_boot_partition(device)
    if boot_partition is None:
        error("ERROR: Failed to determine boot partition")
    print(f"Boot partition: {boot_partition}")
    root_partition = get_root_partition(device)
    if root_partition is None:
        error("ERROR: Failed to determine root partition")
    print(f"Root partition: {root_partition}")
    # try:
    #     mount(root_partition, ROOT_MOUNT)
    # finally:
    #     unmount(ROOT_MOUNT)
