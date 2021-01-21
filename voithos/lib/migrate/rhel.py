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
    debug,
)


class FailedMount(Exception):
    """ A mount operation has failed """


class RhelWorker:
    """ Operate on mounted RedHat systems """

    def __init__(self, devices):
        """Operate on mounted RedHat systems
        Accepts a collection of devices to operate upon
        """
        debug(f"Initiating RhelWorker with devices: {devices}")
        self.devices = devices
        # - property value placeholders -
        # This pattern should help to prevent repeated system queries and improve debug clarity
        self._fdisk_partitions = []
        self._lvm_pvs = []
        self._lvm_lvs = {}
        self._blkid = {}
        self._data_volumes = []
        self._root_volume = ""
        self._boot_partition_is_on_root_volume = False
        self._has_run_dir = None  # boolean when set
        self._fstab = []
        self._boot_volume = ""
        self._boot_mode = ""
        # - constants -
        self.MOUNT_BASE = "/convert"
        self.ROOT_MOUNT = f"{self.MOUNT_BASE}/root"
        # - init logic -
        # if the root volume is already mounted when this starts, find it, else leave it as = ""

    @property
    def fdisk_partitions(self):
        """ return list of partitions on devices """
        if self._fdisk_partitions:
            return self._fdisk_partitions
        debug("---- START: FINDING FDISK PARTITIONS ----")
        partitions = []
        for device in self.devices:
            fdisk = run(f"fdisk -l {device}")
            partition_lines = (line for line in fdisk if line.startswith(device))
            for partition_line in partition_lines:
                partitions.append(partition_line.split(" ")[0])
        self._fdisk_partitions = partitions
        debug("---- DONE: FINDING FDISK PARTITIONS ----")
        return partitions

    @property
    def lvm_pvs(self):
        """ Return a list of physical volumes (partitions) from LVM that match given devices """
        if self._lvm_pvs:
            return self._lvm_pvs
        debug("---- START: FINDING LVM PV'S ----")
        pvs = []
        pvs_lines = run("pvs")
        for line in pvs_lines:
            partition = line.strip().split(" ")[0]
            if "/dev/" not in partition:
                continue
            if partition in self.fdisk_partitions:
                pvs.append(partition)
                self._lvm_pvs = pvs
        debug("---- DONE: FINDING LVM PV'S ----")
        return pvs

    @property
    def lvm_lvs(self):
        """Return a dict of of LVM logical volumes on the given devices
        {"<device mapper path>": { name: "<name>", devices: [<partitions/PVs>] }}
        """
        if self._lvm_lvs:
            return self._lvm_lvs
        debug("---- START: FINDING LVM LV's ----")
        lvs = {}
        for lvm_pv in self.lvm_pvs:
            pv_lines = run(f"pvdisplay -m {lvm_pv}")
            pv_lv_lines = [line for line in pv_lines if "Logical volume" in line]
            # pv_lv_lines looks like this: ['    Logical volume\t/dev/vg_rhel610/lv_root']
            for pv_lv in pv_lv_lines:
                # example's name is /dev/vg_rhel610/lv_root
                name = pv_lv.strip().split("\t")[1]
                # example dmpath is /dev/mapper/vg_rhel610-lv_root
                name_split = name.split("/")
                dm_path = f"/dev/mapper/{name_split[-2]}-{name_split[-1]}"
                if dm_path not in lvs:
                    # First time encountering this LV
                    lvs[dm_path] = {"name": name, "devices": [lvm_pv]}
                else:
                    # This LV was in a prior device, just add this device to it
                    lvs[dm_path]["devices"].append(lvm_pv)
        self._lvm_lvs = lvs
        debug("---- DONE: FINDING LVM LV's ----")
        return lvs

    @property
    def blkid(self):
        """Return the blkid output of each device in devices
        {"<device>": {"UUID": "<UUID">", "TYPE": "<TYPE>"}

        blkid is used to get the filesystem and UUID of a block device
        """
        if self._blkid:
            return self._blkid
        debug("---- START: QUERY BLKID DATA ----")
        _blkid = {}
        blkid_lines = run("blkid")

        def blkid_val(line, prop):
            """ Return the blkid property value if present else none """
            word = next((elem for elem in line.split(" ") if f"{prop}=" in elem), None)
            if word:
                return word.split("=")[1].replace('"', "")
            return None

        for line in blkid_lines:
            split = line.split(" ")
            path = split[0].replace(":", "")
            if path not in self.fdisk_partitions and path not in self.lvm_lvs:
                # This isn't one of the volumes we're currently working with
                continue
            uuid = blkid_val(line, "UUID")
            type_ = blkid_val(line, "TYPE")
            _blkid[path] = {"UUID": uuid, "TYPE": type_}
        self._blkid = _blkid
        debug("---- DONE: QUERY BLKID DATA ----")
        return _blkid

    @property
    def data_volumes(self):
        """Return a list of valid data volume paths:
        Physical (fdisk) partitions that are not LVM PV's, and LVM LVs - no swap
        """
        if self._data_volumes:
            return self._data_volumes
        self._data_volumes = [
            vol
            for vol in (self.fdisk_partitions + list(self.lvm_lvs.keys()))
            if not vol in self.lvm_pvs and self.blkid[vol]["TYPE"] != "swap"
        ]
        return self._data_volumes

    @property
    def root_volume(self):
        """ Return the path to the volume: the volume that contains /etc/fstab """
        if self._root_volume:
            # self._root_volume can be set here or during __init__()
            return self._root_volume
        debug("---- START: LOOKING FOR ROOT VOLUME ----")
        _root_volume = None
        for vol_path in self.data_volumes:
            try:
                mount(vol_path, self.ROOT_MOUNT)
                fstab_path = f"{self.ROOT_MOUNT}/etc/fstab"
                debug(f"Checking for {fstab_path}")
                if Path(fstab_path).exists():
                    if _root_volume:
                        error("ERROR: 2 root vols found: {_root_volume} and {vol_path}", exit=True)
                    else:
                        _root_volume = vol_path
            finally:
                unmount(self.ROOT_MOUNT)
        self._root_volume = _root_volume
        debug(f"---- DONE: LOOKING FOR ROOT VOLUME (...it was {_root_volume}) ----")
        if not _root_volume:
            error(f"ERROR: Failed to find a root volume on devices: {self.devices}")
        return _root_volume

    @staticmethod
    def get_mounted_device_path(mountpoint):
        """ Get the mounted root device path if it exists, else return an empty string """
        debug(f"---- START: CHECKING FOR DEVICE MOUNTED TO {mountpoint} ----")
        mount_lines = run("mount")
        device = next(
            (
                line.split(" ")[0]
                for line in mount_lines
                if len(line.split(" ")) > 3 and line.split(" ")[2] == mountpoint
            ),
            "",
        )
        debug(f"---- DONE: CHECKING FOR DEVICE MOUNTED TO {mountpoint} ({device})----")
        return device

    @property
    def is_root_mounted(self):
        return self.get_mounted_device_path(self.ROOT_MOUNT) != ""

    def mount_root(self):
        """ Mount the root device if it isn't mounted """
        if not self.is_root_mounted:
            debug("mounting root")
            mount(self.root_volume, self.ROOT_MOUNT)
        else:
            debug("mounting root: Already mounted")

    def unmount_root(self):
        """ Unmount the root device """
        debug("Unmounting root")
        unmount(self.ROOT_MOUNT, fail=False)

    @property
    def fstab(self):
        """Return the parsed content of the root volume's /etc/fstab file.
        Parses UUIDs into device paths, quits with an error if that fails.
        Return value is a list of dicts with the following keys:
          - path
          - mountpoint
          - fstype
          - options
        """
        if self._fstab:
            return self._fstab
        debug("---- START: PARSING /etc/fstab FROM ROOT VOLUME ----")
        _fstab = []
        try:
            self.mount_root()
            fstab_lines = get_file_contents(f"{self.ROOT_MOUNT}/etc/fstab").replace("\t", "")
            debug("/etc/fstab contents:")
            debug(fstab_lines)
            for line in fstab_lines.split("\n"):
                # Skip comments, swap tabs with spaces
                line = line.strip().replace("\t", "")
                if line.startswith("#"):
                    continue
                split = [word for word in line.split(" ") if word]
                if len(split) < 3:
                    continue
                path = split[0]
                if path.startswith("UUID="):
                    uuid = path.split("=")[1]
                    debug(f"fstab line has UUID: {line}")
                    path = next(
                        (path for path in self.blkid if self.blkid[path]["UUID"] == uuid), None
                    )
                    if path is None:
                        error(f"ERROR: Failed to find path to fstab UUID in {line}", exit=True)
                    debug(f"Mapped UUID {uuid} to device path: {path}")
                elif not path.startswith("/"):
                    debug(f"Skipping /etc/fstab system path: {path}")
                    continue
                _fstab.append(
                    {
                        "path": path,
                        "mountpoint": split[1],
                        "fstype": split[2],
                        "options": split[3] if len(split) > 3 else "",
                    }
                )
        finally:
            self.unmount_root()
        debug("---- DONE: PARSING /etc/fstab FROM ROOT VOLUME ----")
        self._fstab = _fstab
        return _fstab

    @property
    def boot_partition_is_on_root_volume(self):
        """ Return bool - If there is no /boot in fstab, then it's on the root partition """
        if self._boot_partition_is_on_root_volume:
            return self._boot_partition_is_on_root_volume
        debug("---- START: CHECKING IF /BOOT IS ON THE ROOT PARTITION ----")
        boot_entry = next((entry for entry in self.fstab if entry["mountpoint"] == "/boot"), None)
        is_on_root = boot_entry is None
        debug(f"---- DONE: CHECKING IF /BOOT IS ON THE ROOT PARTITION ({is_on_root})----")
        self._boot_partition_is_on_root_volume = is_on_root
        return is_on_root

    @property
    def has_run_dir(self):
        """ Return bool does this system have a /run dir? RHEL 6 sometimes doesn't """
        if self._has_run_dir != None:
            return self._has_run_dir
        try:
            if not self.was_root_vol_mounted:
                mount(self.root_volume, self.ROOT_MOUNT)
            self._has_run_dir = Path(f"{self.ROOT_MOUNT}/run").exists()
        finally:
            if not self.was_root_vol_mounted:
                unmount(self.ROOT_MOUNT)
        return self._has_run_dir

    @property
    def boot_volume(self):
        """ Return the path of the boot volume """
        if self._boot_volume:
            return self._boot_volume
        if self.boot_partition_is_on_root_volume:
            error("ERROR: /boot is on the root partition, there is no boot volume", exit=True)
        debug("---- START: LOCATING BOOT VOLUME ----")
        boot_entry = next(entry for entry in self.fstab if entry["mountpoint"] == "/boot")
        boot_vol_path = boot_entry["path"]
        self._boot_volume = boot_entry["path"]
        debug(f"---- DONE: LOCATING BOOT VOLUME ({self._boot_volume}) ----")
        return boot_entry["path"]

    @property
    def boot_mode(self):
        """ Return either "UEFI" or "BIOS" - Determine how this device boots """
        if self._boot_mode:
            return self._boot_mode
        debug("---- START: DETERMINING BOOT MODE ----")
        # Get the disk of the boot partition, ex /dev/vdb for /dev/vdb1
        drive = "".join([char for char in self.boot_volume if not char.isdigit()])
        # Read fdisk's Disklabel for the disk
        fdisk = run(f"fdisk -l {drive}")
        disk_type_line = next((line for line in fdisk if "Disklabel type" in line), None)
        if disk_type_line is None:
            error(f"Error: Failed to determine boot mode of {self.boot_volume}", exit=True)
        disk_type = disk_type_line.split(" ")[-1]
        _boot_mode = "UEFI" if (disk_type == "gpt") else "BIOS"
        self._boot_mode = _boot_mode
        debug(f"---- DONE: DETERMINING BOOT MODE ({_boot_mode}) ----")
        return _boot_mode

    def get_ordered_mount_opts(self, reverse=False):
        """Return the order of volumes to be mounted/unmounted, in the order ftab returned them
        Returns list of dicts with these keys:
            { "mnt_from": "<path>", "mnt_to": "<path>", "bind": <bool> }
        """
        mount_opts = []
        try:
            self.mount_root()
            mountpoints = [
                entry["mountpoint"]
                for entry in self.fstab
                if entry["mountpoint"] != "swap" and entry["mountpoint"].startswith("/")
            ]
            for mpoint in mountpoints:
                fstab_entry = next(entry for entry in self.fstab if entry["mountpoint"] == mpoint)
                if fstab_entry["mountpoint"] == "/":
                    # Handle root mount differently - it goes to ROOT_MOUNT and doesn't have a bind
                    mount_opts.append(
                        {"mnt_from": fstab_entry["path"], "mnt_to": self.ROOT_MOUNT, "bind": False}
                    )
                    continue
                debug(fstab_entry)
                if "bind" not in fstab_entry["options"]:
                    device = fstab_entry["path"]
                    # Before vol can be mounted to the chroot it needs to be mounted to the worker
                    # the sys_mountpoint of /var/tmp would be /convert/var_tmp
                    subpath = fstab_entry["mountpoint"][1:].replace("/", "_")
                    sys_mountpoint = f"{self.MOUNT_BASE}/{subpath}"
                    mount_opts.append(
                        {"mnt_from": fstab_entry["path"], "mnt_to": sys_mountpoint, "bind": False}
                    )
                    # then bind-mind the volume into the chroot (remove first char / from mpoint)
                    chroot_bind_path = f"{self.ROOT_MOUNT}/{fstab_entry['mountpoint'][1:]}"
                    mount_opts.append(
                        {"mnt_from": sys_mountpoint, "mnt_to": chroot_bind_path, "bind": True}
                    )
                else:
                    # This is a bind mount, so just link the dirs in the chroot
                    chroot_src = f"{self.ROOT_MOUNT}/{fstab_entry['path']}"
                    chroot_dest = f"{self.ROOT_MOUNT}/{fstab_entry['mountpoint']}"
                    mount_opts.append({"mnt_from": chroot_src, "mnt_to": chroot_dest, "bind": True})
            devpaths = ["/sys", "/proc", "/dev"]
            if self._has_run_dir:
                devpaths.append("/run")
            for devpath in devpaths:
                chroot_devpath = f"{self.ROOT_MOUNT}{devpath}"
                mount_opts.append({"mnt_from": devpath, "mnt_to": chroot_devpath, "bind": True})
        finally:
            self.unmount_root()
        if reverse:
            mount_opts.reverse()
        return mount_opts

    def unmount_volumes(self, prompt=False, print_progress=False):
        """ Unount the /etc/fstab and device volumes from the chroot root dir """
        debug(f"---- START: UNMOUNTING ALL VOLUMES ----")
        for mount_opts in self.get_ordered_mount_opts(reverse=True):
            debug("Unmount: {mount_opts['mount_to']}")
            if print_progress:
                print(f"Unmount: {mount_opts['mnt_to']}")
            unmount(mount_opts["mnt_to"], prompt=prompt, fail=prompt)
        debug(f"---- DONE: UNMOUNTING ALL VOLUMES ----")

    def mount_volumes(self, print_progress=False):
        """ Mount the /etc/fstab and device volumes into the chroot root dir """
        debug(f"---- START: MOUNTING ALL VOLUMES ----")
        debug("Unmount all volumes before mounting to ensure clean env")
        self.unmount_volumes(prompt=True, print_progress=False)
        # Mount the root volume
        if not self.is_root_mounted:
            debug(f"Mounting root volume {self.root_volume} to {self.ROOT_MOUNT}")
            mount(self.root_volume, self.ROOT_MOUNT)
            if print_progress:
                print(f"mount {self.root_volume} {self.ROOT_MOUNT}")
        # Mount the other volumes
        for mount_opts in self.get_ordered_mount_opts():
            if mount_opts["mnt_to"] == self.ROOT_MOUNT:
                continue
            if print_progress:
                bind = "--bind" if mount_opts["bind"] else ""
                print(f"mount {mount_opts['mnt_from']} {mount_opts['mnt_to']} {bind}")
            mount(mount_opts["mnt_from"], mount_opts["mnt_to"], bind=mount_opts["bind"])
        debug(f"---- DONE: MOUNTING ALL VOLUMES ----")

    def add_virtio_drivers(self):
        """ Install VirtIO drivers to mounted system """
        debug(f"---- START: ADD VIRTIO DRIVERS ----")
        try:
            self.mount_volumes()
        finally:
            self.unmount_volumes()
        debug(f"---- DONE: ADD VIRTIO DRIVERS ----")


##########

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


def _is_initrd_file(file_name):
    """ Return Boolean, is the given filename an initrd file? """
    return file_name.startswith("initramfs-") and file_name.endswith(".img")


def get_initrd_data():
    """ Find the path and kernel version of each initrd file on the mounted system """
    ls_boot = chroot_run("ls /boot")
    initrd_files = [fname for fname in ls_boot if _is_initrd_file(fname)]
    data = {}
    for initrd_file in initrd_files:
        kernel_ver = initrd_file.replace("initramfs-", "").replace(".img", "")
        data[kernel_ver] = f"/boot/{initrd_file}"
    if not data:
        error("ERROR: Failed to detect initrd data", exit=True)
    return data



###########################################


# Mountpoints for volume work to be done
MOUNT_BASE = "/convert"
ROOT_MOUNT = f"{MOUNT_BASE}/root"

EFI_MOUNT = f"{MOUNT_BASE}/efi"
BOOT_MOUNT = f"{MOUNT_BASE}/boot"
BOOT_BIND_MOUNT = f"{ROOT_MOUNT}/boot"


def get_partitions(device):
    """ Return a list of partitions on a device """
    fdisk = run(f"fdisk -l {device}")
    partitions = []
    partition_lines = (line for line in fdisk if line.startswith(device))
    for partition_line in partition_lines:
        partitions.append(partition_line.split(" ")[0])
    return partitions


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


def get_device_root_partition(device, fail=True):
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
        error("ERROR: Failed to determine root partition", exit=True)


def get_root_partition(devices):
    """ Find the root partition from a set of devices """
    root_partition = None
    for device in devices:
        device_root = get_device_root_partition(device, fail=False)
        if device_root is not None:
            debug(f"root partition detected on {device} as {device_root}")
        # If there's more than one root partition, something isn't right
        if root_partition and device_root and root_partition != device_root:
            error(f"ERROR: both {root_partition} and {device_root} are root partitions", exit=True)
        if device_root is not None:
            root_partition = device_root
    if root_partition is None:
        error(f"ERROR: Failed to find the root partition in {devices}", exit=True)
    return root_partition


def mkdir(path):
    """ Make a directory and print a debug msg"""
    debug(f"mkdir -p {path}")
    Path(path).mkdir(exist_ok=True)


def get_fstab():
    """ Get the filesystem table data """
    fstab_path = f"{ROOT_MOUNT}/etc/fstab"
    fstab = get_file_contents(fstab_path)
    for line in fstab:
        # skip comments
        line = line.strip()
        if line.startswith("#"):
            continue

def mount_partitions(devices):
    """Mount all the worker partitions
    Accepts a set of devices which might be involved
    ex: mount_partitions( ('/dev/vdb','dev/vdc','/dev/vdd') )
    """
    debug("START mount_partitions")
    # Mount the root partition
    mkdir(MOUNT_BASE)
    mkdir(ROOT_MOUNT)
    root_partition = get_root_partition(devices)
    mount(root_partition, ROOT_MOUNT)
    # Get the fstab file contents
    #
    debug("END mount_partitions")


# mount_partitions(('/dev/vdb','/dev/vdc','/dev/vdd'))


def unmount_partitions():
    """ Unmount all the worker partitions to ensure a clean setup """
    unmount(BOOT_BIND_MOUNT, prompt=True)
    unmount(ROOT_MOUNT, prompt=True)
    unmount(BOOT_MOUNT, prompt=True)
    unmount(EFI_MOUNT, prompt=True)


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


def get_partition_uuid(partition):
    """ Return the UUID of a partition """
    blkid = run(f"blkid {partition}")
    return blkid[0].split(" ")[1].replace("UUID=", "").replace('"', "")


def chroot_run(cmd):
    """ Run a command in the root chroot and return the lines as a list """
    return run(f"chroot {ROOT_MOUNT} {cmd}")


def get_rpm_version(package):
    """ Return the version of the given package - Assumes appropriate mounts are in place """
    query_format = "%{VERSION}-%{RELEASE}.%{ARCH}"
    rpm_lines = chroot_run(f"rpm -q {package} --queryformat {query_format}")
    return rpm_lines[0]




def add_virtio_drivers(device):
    """  Add VirtIO drivers to the specified block device """
    # Validate the connected given device exists
    assert_block_device_exists(device)
    unmount_partitions()
    # Find the boot volume - how that's done varies from BIOS to UEFI
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
        initrd_data = get_initrd_data()
        for kernel_version, initrd_path in initrd_data.items():
            print(f"Injecting VirtIO drivers into {initrd_path}")
            print(f"Kernel version: {kernel_version}")
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
        ('ATTR{address}=="' + mac_addr + '"'),
        f'NAME="{interface_name}"',
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
