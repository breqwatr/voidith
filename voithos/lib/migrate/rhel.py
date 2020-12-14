""" Library for RHEL migration operations """
import os
from pathlib import Path

from voithos.lib.system import (
    error,
    run,
    assert_block_device_exists,
    mount,
    unmount,
    get_file_contents,
    set_file_contents,
)


# Mountpoints for volume work to be done
MOUNT_BASE = "/convert"
EFI_MOUNT = f"{MOUNT_BASE}/efi"
BOOT_MOUNT = f"{MOUNT_BASE}/boot"
ROOT_MOUNT = f"{MOUNT_BASE}/root"
BOOT_BIND_MOUNT = f"{ROOT_MOUNT}/boot"


class FailedMount(Exception):
    """ A mount operation has failed """


def unmount_partitions():
    """ Unmount all the worker partitions to ensure a clean setup """
    unmount(BOOT_BIND_MOUNT, prompt=True)
    unmount(ROOT_MOUNT, prompt=True)
    unmount(BOOT_MOUNT, prompt=True)
    unmount(EFI_MOUNT, prompt=True)


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


def get_efi_partition(device):
    """ Find which partition is the EFI partition """
    fdisk = run(f"fdisk -l {device}")
    efi_line = next(line for line in fdisk if line.startswith(device) and "EFI" in line)
    return efi_line.split(" ")[0]


def get_uefi_boot_partition(device):
    """Return path (str) of boot partition in a UEFI style device
    There's a chance it won't find it. If so, return None.
    """
    efi_partition = get_efi_partition(device)
    try:
        mount(efi_partition, EFI_MOUNT)
        grub_path = f"{EFI_MOUNT}/EFI/redhat/grub.cfg"
        grub_contents = get_file_contents(grub_path, required=True)
        efi_partition = get_efi_partition(device)
        for partition in get_partitions(device):
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


def get_partition_uuid(partition):
    """ Return the UUID of a partition """
    blkid = run(f"blkid {partition}")
    return blkid[0].split(" ")[1].replace("UUID=", "").replace('"', "")


def get_pvs():
    """ Return a list of LVM physical volumes """
    pvs = []
    pv_lines = run("pvdisplay")
    pv_name_lines = [line for line in pv_lines if "PV Name" in line]
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
    lv_lines = [line for line in pv_lines if "Logical volume" in line]
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
    fs_type = elem.replace('"', "").split("=")[1]
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


def get_root_partition(device, fail=True):
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
    if fail:
        # No root partition was found
        error("ERROR: Failed to determine root partition", exit=True)


def chroot_run(cmd):
    """ Run a command in the root chroot and return the lines as a list """
    return run(f"chroot {ROOT_MOUNT} {cmd}")


def get_rpm_version(package):
    """ Return the version of the given package - Assumes appropriate mounts are in place """
    query_format = "%{VERSION}-%{RELEASE}.%{ARCH}"
    rpm_lines = chroot_run(f"rpm -q {package} --queryformat {query_format}")
    return rpm_lines[0]


def is_virtio_driverset_present(initrd_path):
    """ Check if Virtio drivers exist inside the given initrd path - return Boolean"""
    lsinitrd_lines = chroot_run(f"lsinitrd {initrd_path}")
    virtio_lines = [line for line in lsinitrd_lines if "virtio" in line.lower()]
    # If no lines of lsinitrd contain "virtio" then the drivers are not installed
    return len(virtio_lines) != 0


def install_virtio_drivers(initrd_path, kernel_version):
    """ Install VirtIO drivers into the given initrd file """
    # Python+chroot causes the dracut space delimiter to break - circumvented via script file
    drivers = "virtio_blk virtio_net virtio_scsi virtio_balloon"
    cmd = f'dracut --add-drivers "{drivers}" -f {initrd_path} {kernel_version}\n'
    script_file = f"{ROOT_MOUNT}/virtio.sh"
    set_file_contents(script_file, cmd)
    chroot_run("bash /virtio.sh")
    os.remove(script_file)
    if not is_virtio_driverset_present(initrd_path):
        error("ERROR: Failed to install VirtIO drivers", exit=True)


def add_virtio_drivers(device):
    """  Add VirtIO drivers to the specified block device """
    # Validate the connected given device exists
    assert_block_device_exists(device)
    unmount_partitions()
    # Find the boot volume - how that's done varies from BIOS to UEFO
    boot_mode = get_boot_mode(device)
    print(f"Boot Style: {boot_mode}")
    if boot_mode == "BIOS":
        boot_partition = get_bios_boot_partition(device)
    else:
        boot_partition = get_uefi_boot_partition(device)
    if boot_partition is None:
        error("ERROR: Failed to determine boot partition", exit=True)
    print(f"Boot partition: {boot_partition}")
    # Find the root volume
    root_partition = get_root_partition(device)
    print(f"Root partition: {root_partition}")
    # Setup the mounts, bind-mounting boot to root, and install the virtio drivers
    try:
        mount(boot_partition, BOOT_MOUNT)
        mount(root_partition, ROOT_MOUNT)
        mount(BOOT_MOUNT, BOOT_BIND_MOUNT, bind=True)
        kernel_version = get_rpm_version("kernel")
        print(f"Kernel version: {kernel_version}")
        initrd_path = f"/boot/initramfs-{kernel_version}.img"
        print(f"Checking {initrd_path} from {boot_partition} for VirtIO drivers")
        if is_virtio_driverset_present(initrd_path):
            print("Virtio drivers are already installed")
        else:
            print("Installing VirtIO drivers - please wait")
            install_virtio_drivers(initrd_path, kernel_version)
            print("Finished installing VirtIO drivers")
    finally:
        unmount(BOOT_BIND_MOUNT, fail=False)
        unmount(ROOT_MOUNT, fail=False)
        unmount(BOOT_MOUNT)


def repair_partition(partition, file_system):
    """ Repair a given partition using the appropriate tool"""
    if file_system == "xfs":
        print(f" > Repairing XFS partition {partition}")
        run(f"xfs_repair {partition}")
    elif "ext" in file_system:
        print(f" > Repairing {file_system} partition {partition}")
        repair_cmd = f"fsck.{file_system} -y {partition}"
        run(repair_cmd)
    else:
        print(f" > Cannot repair {file_system} partitions")


def repair_partitions(device):
    """ Attempt to repair paritions of supported filesystems on this device """
    unmount_partitions()
    for partition in get_partitions(device):
        file_system = get_fs_type(partition)
        print(f"Partition: {partition} - FileSystem: {file_system}")
        if "lvm" in file_system.lower():
            for lvm_vol in get_logical_volumes(partition):
                lv_fs = get_fs_type(lvm_vol["dm"])
                print(f"Logical Volume: {lvm_vol['lv']} - FileSystem {lv_fs}")
                repair_partition(lvm_vol["dm"], lv_fs)
                print("")
        else:
            repair_partition(partition, file_system)
            print("")
    print("Finished repairing supported partitions")


def uninstall(device, package, like=False):
    """ Uninstall the specified package. When like is True, remove all packages like it """
    root_partition = get_root_partition(device)
    print(f"Root partition: {root_partition}")
    try:
        mount(root_partition, ROOT_MOUNT)
        if not like:
            print(f"Uninstalling: {package}")
            chroot_run(f"rpm -e {package}")
            return
        # rpm -qa | grep "vm-tools" | while read pkg; do echo "removing $pkg"; rpm -e $pkg; done
        rpm_lines = chroot_run("rpm -qa")
        rpms = [line for line in rpm_lines if package in line]
        if not rpms:
            print(f'No packages were found matching "{package}"')
            return
        for rpm in rpms:
            print(f"Uninstalling: {rpm}")
            chroot_run(f"rpm -e {rpm}")
    finally:
        unmount(ROOT_MOUNT)


def create_interface_file(
    root_partition,
    name,
    is_dhcp,
    mac_addr,
    ip_addr=None,
    prefix=None,
    gateway=None,
    dns=(),
    domain=None,
):
    """ Deploy a network interface file to the root partition """
    bootproto = "dhcp" if is_dhcp else "static"
    lines = [
        f"DEVICE={name}",
        f"BOOTPROTO={bootproto}",
        "ONBOOT=yes",
        "USERCTL=no",
        f"HWARDDR={mac_addr}",
    ]
    if not is_dhcp:
        lines.append(f"IPADDR={ip_addr}")
        lines.append(f"PREFIX={prefix}")
        if gateway is not None:
            lines.append("DEFROUTE=yes")
            lines.append(f"GATEWAY={gateway}")
    for index, domain_server in enumerate(dns):
        num = index + 1
        lines.append(f"DNS{num}={domain_server}")
    if domain is not None:
        lines.append(f"DOMAIN={domain}")
    contents = "\n".join(lines)
    path = f"{ROOT_MOUNT}/etc/sysconfig/network-scripts/ifcfg-{name}"
    print(f"Creating interface file at {path}:")
    print(contents)
    set_file_contents(path, contents)


def create_udev_interface_rule(root_partition, mac_addr, interface_name):
    """ Create a udev rule in the root partition ensuring that a mac addr gets the right name """
    path = f"{ROOT_MOUNT}/etc/udev/rules.d/70-persistent-net.rules"
    contents = get_file_contents(path)
    for line in contents:
        if interface_name in contents:
            error(f"\nERROR: '{interface_name}' found in {path} - to resolve, remove it:")
            error(f" > mount {root_partition} {ROOT_MOUNT}")
            error(f" > vi {path}")
            error(f" > umount {ROOT_MOUNT}", exit=True)
    # {address} is meant to look like that, it is not an f-string missing its f
    parts = [
        'SUBSYSTEM=="net"',
        'ACTION=="add"',
        'DRIVERS=="?*"',
        ('ATTR{address}=="' + mac_addr),
        f"NAME=\"{interface_name}\"",
    ]
    # Join the entries to looks like 'SUBSYSTEM=="net", ACTION=="add",...' with a \n at the end
    line = ", ".join(parts) + "\n"
    print("")
    print(f"Appending udev rule to {path}:")
    print(line)
    set_file_contents(path, line, append=True)
    print("udev file contents:")
    print(get_file_contents(path))


def set_udev_interface(
    device,
    interface_name,
    is_dhcp,
    mac_addr,
    ip_addr=None,
    prefix=None,
    gateway=None,
    dns=(),
    domain=None,
):
    """ Deploy a udev rule and interface file to ensure a predictable network config """
    unmount_partitions()
    root_partition = get_root_partition(device)
    try:
        mount(root_partition, ROOT_MOUNT)
        create_interface_file(
            root_partition,
            interface_name,
            is_dhcp,
            mac_addr,
            ip_addr=ip_addr,
            prefix=prefix,
            gateway=gateway,
            dns=dns,
            domain=domain,
        )
        create_udev_interface_rule(root_partition, mac_addr, interface_name)
    finally:
        unmount(ROOT_MOUNT)
