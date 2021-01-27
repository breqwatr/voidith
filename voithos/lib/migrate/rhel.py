""" Library for RHEL migration operations """
import os
from pathlib import Path
from voithos.lib.system import (
    error,
    run,
    assert_block_device_exists,
    mount,
    unmount,
    is_mounted,
    get_mount,
    get_file_contents,
    set_file_contents,
    debug,
)


class RhelWorker:
    """ Operate on mounted RedHat systems """

    def __init__(self, devices=None):
        """Operate on mounted RedHat systems
        Accepts a collection of devices to operate upon
        """
        debug(f"Initiating RhelWorker with devices: {devices}")
        self.devices = devices
        # - property value placeholders -
        # This pattern should help to prevent repeated system queries and improve debug clarity
        self._was_root_mounted = None  # Bool
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
        self.debug_task = []  # Keeps track of current state for troubleshooting
        # - constants -
        self.MOUNT_BASE = "/convert"
        self.ROOT_MOUNT = f"{self.MOUNT_BASE}/root"
        # init
        self._was_root_mounted = self.was_root_mounted

    def debug_action(self, action=None, end=False):
        """ Write a debug message tracking what's going on here """
        if end:
            breadcrumbs = " > ".join(self.debug_task)
            debug(f"---- DONE:  {breadcrumbs}")
            self.debug_task.pop()
            if self.debug_task:
                breadcrumbs = " > ".join(self.debug_task)
                debug(f"---- CONT:  {breadcrumbs}")
            else:
                debug("---- DONE!")
        else:
            self.debug_task.append(action.upper())
            breadcrumbs = " > ".join(self.debug_task)
            debug(f"---- START: {breadcrumbs}")

    @property
    def was_root_mounted(self):
        """ Check if root was mounted when this started """
        if self._was_root_mounted is not None:
            return self._was_root_mounted
        is_root_mounted = is_mounted(self.ROOT_MOUNT)
        self._wwas_root_mounted = is_root_mounted
        return is_root_mounted

    @property
    def fdisk_partitions(self):
        """ return list of partitions on devices """
        if self._fdisk_partitions:
            return self._fdisk_partitions
        self.debug_action(action="FIND FDISK PARTITIONS")
        partitions = []
        if not self.devices:
            error("ERROR: Cannot list partitions when devices are not specified", exit=True)
        for device in self.devices:
            fdisk = run(f"fdisk -l {device}")
            partition_lines = (line for line in fdisk if line.startswith(device))
            for partition_line in partition_lines:
                partitions.append(partition_line.split(" ")[0])
        self._fdisk_partitions = partitions
        debug(f"fdisk_partitions: {partitions}")
        self.debug_action(end=True)
        return partitions

    @property
    def lvm_pvs(self):
        """ Return a list of physical volumes (partitions) from LVM that match given devices """
        if self._lvm_pvs:
            return self._lvm_pvs
        self.debug_action(action="FIND LVM PV's")
        pvs = []
        pvs_lines = run("pvs")
        for line in pvs_lines:
            partition = line.strip().split(" ")[0]
            if "/dev/" not in partition:
                continue
            if partition in self.fdisk_partitions:
                pvs.append(partition)
                self._lvm_pvs = pvs
        self.debug_action(end=True)
        return pvs

    @property
    def lvm_lvs(self):
        """Return a dict of of LVM logical volumes on the given devices
        {"<device mapper path>": { name: "<name>", devices: [<partitions/PVs>] }}
        """
        if self._lvm_lvs:
            return self._lvm_lvs
        self.debug_action(action="FIND LVM LV's")
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
        self.debug_action(end=True)
        return lvs

    @property
    def blkid(self):
        """Return the blkid output of each device in devices
        {"<device>": {"UUID": "<UUID">", "TYPE": "<TYPE>"}

        blkid is used to get the filesystem and UUID of a block device
        """
        if self._blkid:
            return self._blkid
        self.debug_action(action="GET BLKID DATA")
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
            if not split[0]:
                continue
            path = split[0].replace(":", "")
            uuid = blkid_val(line, "UUID")
            type_ = blkid_val(line, "TYPE")
            _blkid[path] = {"UUID": uuid, "TYPE": type_}
        self._blkid = _blkid
        for device in _blkid:
            debug(f"{device}: {_blkid[device]}")
        self.debug_action(end=True)
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
        self.debug_action(action="FIND ROOT VOLUME")
        fstab_path = f"{self.ROOT_MOUNT}/etc/fstab"
        if is_mounted(self.ROOT_MOUNT):
            # something's already mounted to ROOT_MOUNT, validate it
            fstab_contents = get_file_contents(fstab_path)
            if not fstab_contents:
                error("ERROR: Mounted root volume has no /etc/fstab", exit=True)
            device = get_mount(self.ROOT_MOUNT)["device"]
            self._root_volume = device
            debug(device)
            self.debug_action(end=True)
            return device
        if self.devices is None:
            error(f"ERROR: Failed to find root partition - no devices specified", exit=True)
        _root_volume = None
        # root volume wasn't mounted, mount each data volume until you find /etc/fstab
        for vol_path in self.data_volumes:
            debug(f"Checking for /etc/fstab in {vol_path}")
            try:
                mount(vol_path, self.ROOT_MOUNT)
                if get_file_contents(fstab_path):
                    self._root_volume = vol_path
                    unmount(self.ROOT_MOUNT)
                    _root_volume = vol_path
                    break
            finally:
                unmount(self.ROOT_MOUNT)
        debug(f"> root volume =  {_root_volume}")
        self.debug_action(end=True)
        if _root_volume is None:
            error(f"ERROR: Failed to find a root volume on devices: {self.devices}", exit=True)
        self._root_volume = _root_volume
        return _root_volume

    def mount_root(self):
        """ Mount the root device if it isn't mounted """
        mount(self.root_volume, self.ROOT_MOUNT)

    def unmount_root(self):
        """ Unmount the root device """
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
        self.debug_action(action="PARSE FSTAB")
        _fstab = []
        try:
            if not self.was_root_mounted:
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
                    debug(f"fstab line has UUID: {uuid}")
                    debug(line)
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
            if not self.was_root_mounted:
                self.unmount_root()
        self.debug_action(end=True)
        self._fstab = _fstab
        return _fstab

    @property
    def boot_partition_is_on_root_volume(self):
        """ Return bool - If there is no /boot in fstab, then it's on the root partition """
        if self._boot_partition_is_on_root_volume:
            return self._boot_partition_is_on_root_volume
        self.debug_action(action="CHECK IF /BOOT ON /ROOT")
        boot_entry = next((entry for entry in self.fstab if entry["mountpoint"] == "/boot"), None)
        is_on_root = boot_entry is None
        self.debug_action(end=True)
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
        self.debug_action(action="LOCATE BOOT VOLUME")
        boot_entry = next(entry for entry in self.fstab if entry["mountpoint"] == "/boot")
        boot_vol_path = boot_entry["path"]
        self._boot_volume = boot_entry["path"]
        self.debug_action(end=True)
        return boot_entry["path"]

    @property
    def boot_mode(self):
        """ Return either "UEFI" or "BIOS" - Determine how this device boots """
        if self._boot_mode:
            return self._boot_mode
        self.debug_action(action="FIND BOOT MODE")
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
        self.debug_action(end=True)
        return _boot_mode

    def get_ordered_mount_opts(self, reverse=False):
        """Return the order of volumes to be mounted/unmounted, in the order ftab returned them
        This is the lengthy logic where the /etc/fstab file gets parsed out
        Returns list of dicts with these keys:
            { "mnt_from": "<path>", "mnt_to": "<path>", "bind": <bool> }
        """
        self.debug_action(action="GET ORDERED MOUNT OPTIONS")
        mount_opts = []
        try:
            if not self.was_root_mounted:
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
                debug(f"FSTAB ENTRY: {fstab_entry}")
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
            if not self.was_root_mounted:
                self.unmount_root()
        if reverse:
            mount_opts.reverse()
        self.debug_action(end=True)
        return mount_opts

    def unmount_volumes(self, prompt=False, print_progress=False):
        """ Unmount the /etc/fstab and device volumes from the chroot root dir """
        self.debug_action(action="UNMOUNT ALL VOLUMES")
        for mount_opts in self.get_ordered_mount_opts(reverse=True):
            debug(f"Unmount: {mount_opts['mnt_to']}")
            if print_progress:
                print(f"umount {mount_opts['mnt_to']}")
            unmount(mount_opts["mnt_to"], prompt=prompt, fail=prompt)
        self.debug_action(end=True)

    def mount_volumes(self, print_progress=False):
        """ Mount the /etc/fstab and device volumes into the chroot root dir """
        self.debug_action(action="MOUNT ALL VOLUMES")
        # Mount the root volume
        debug("Collect the ordered mount options")
        ordered_mount_opts = self.get_ordered_mount_opts()  # unmounts root
        debug(f"Mounting root volume {self.root_volume} to {self.ROOT_MOUNT}")
        mount(self.root_volume, self.ROOT_MOUNT)
        if print_progress:
            print(f"mount {self.root_volume} {self.ROOT_MOUNT}")
        # Mount the other volumes
        for mount_opts in ordered_mount_opts:
            if mount_opts["mnt_to"] == self.ROOT_MOUNT:
                continue
            if print_progress:
                bind = "--bind" if mount_opts["bind"] else ""
                print(f"mount {mount_opts['mnt_from']} {mount_opts['mnt_to']} {bind}")
            mount(mount_opts["mnt_from"], mount_opts["mnt_to"], bind=mount_opts["bind"])
        self.debug_action(end=True)

    def chroot_run(self, cmd):
        """ Run a command in the chroot """
        return run(f"chroot {self.ROOT_MOUNT} {cmd}")

    def add_virtio_drivers(self, force=False):
        """ Install VirtIO drivers to mounted system """
        if not self.was_root_mounted:
            error("ERROR: You must mount the volumes before you can add virtio drivers", exit=True)
        self.debug_action(action="ADD VIRTIO DRIVERS")
        ls_boot_lines = run(f"ls {self.ROOT_MOUNT}/boot")
        initram_lines = [
            line
            for line in ls_boot_lines
            if line.startswith("initramfs-") and line.endswith(".img") and "dump" not in line
        ]
        for filename in initram_lines:
            kernel_version = filename.replace("initramfs-", "").replace(".img", "")
            debug("Running lsinitrd to check for virtio drivers")
            lsinitrd = self.chroot_run(f"lsinitrd /boot/{filename}")
            virtio_line = next((line for line in lsinitrd if "virtio" in line.lower()), None)
            if virtio_line is not None:
                print(f"{filename} already has virtio drivers")
                if force:
                    print("force=true, reinstalling")
                else:
                    continue
            print(f"Adding virtio drivers to {filename}")
            drivers = "virtio_blk virtio_net virtio_scsi virtio_balloon"
            cmd = f'dracut --add-drivers "{drivers}" -f /boot/{filename} {kernel_version}'
            # Python+chroot causes dracut space delimiter to break - use a script file
            script_file = f"{self.ROOT_MOUNT}/virtio.sh"
            debug(f"writing script file: {script_file}")
            debug(f"script file contents: {cmd}")
            set_file_contents(script_file, cmd)
            self.chroot_run("bash /virtio.sh")
            debug(f"deleting script file: {script_file}")
            os.remove(script_file)
        self.debug_action(end=True)

    def uninstall(self, package, like=False):
        """ Uninstall packages from the given system """
        if not like:
            print(f"Uninstalling: {package}")
            self.chroot_run(f"rpm -e {package}")
            return
        rpm_lines = self.chroot_run("rpm -qa")
        rpms = [line for line in rpm_lines if package in line]
        if not rpms:
            print(f'No packages were found matching "{package}"')
            return
        for rpm in rpms:
            print(f"Uninstalling: {rpm}")
            self.chroot_run(f"rpm -e {rpm}")

    def repair_partitions(self):
        """ Repair a given partition using the appropriate tool"""
        if is_mounted(self.ROOT_MOUNT):
            error("ERROR: Cannot repair partitions when they are mounted", exit=True)
        for partition in self.data_volumes:
            filesystem = self.blkid[partition]["TYPE"]
            if filesystem == "xfs":
                print(f" > Repairing XFS partition {partition}")
                run(f"xfs_repair {partition}")
            elif "ext" in filesystem:
                print(f" > Repairing {filesystem} partition {partition}")
                repair_cmd = f"fsck.{filesystem} -y {partition}"
                run(repair_cmd)
            else:
                print(f" ! Cannot repair {partition} - unsupported filesystem: {filesystem}")

    def set_udev_interface(
        self,
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
        # create the /etc/sysconfig/network-scripts file
        bootproto = "dhcp" if is_dhcp else "static"
        iface_lines = [
            f"DEVICE={interface_name}",
            f"BOOTPROTO={bootproto}",
            "ONBOOT=yes",
            "USERCTL=no",
            f"HWARDDR={mac_addr}",
        ]
        if not is_dhcp:
            iface_lines.append(f"IPADDR={ip_addr}")
            iface_lines.append(f"PREFIX={prefix}")
            if gateway is not None:
                iface_lines.append("DEFROUTE=yes")
                iface_lines.append(f"GATEWAY={gateway}")
        for index, domain_server in enumerate(dns):
            num = index + 1
            iface_lines.append(f"DNS{num}={domain_server}")
        if domain is not None:
            iface_lines.append(f"DOMAIN={domain}")
        iface_contents = "\n".join(iface_lines)
        iface_path = f"{self.ROOT_MOUNT}/etc/sysconfig/network-scripts/ifcfg-{interface_name}"
        print(f"Creating interface file at {iface_path}:")
        print(iface_contents)
        set_file_contents(iface_path, iface_contents)
        # Create the udev rule to set the interface name
        udev_path = f"{self.ROOT_MOUNT}/etc/udev/rules.d/70-persistent-net.rules"
        udev_contents = get_file_contents(udev_path)
        for line in udev_contents:
            if interface_name in line:
                error(f"ERROR: '{interface_name}' in {udev_path} - remove to continue", exit=True)
        # {address} is meant to look like that, it is not an f-string missing its f
        udev_parts = [
            'SUBSYSTEM=="net"',
            'ACTION=="add"',
            'DRIVERS=="?*"',
            ('ATTR{address}=="' + mac_addr + '"'),
            f'NAME="{interface_name}"',
        ]
        # Join the entries to looks like 'SUBSYSTEM=="net", ACTION=="add",...' with a \n at the end
        udev_line = ", ".join(udev_parts) + "\n"
        print("")
        print(f"Appending udev rule to file: {udev_path}")
        print(udev_line)
        set_file_contents(udev_path, udev_line, append=True)
        print("udev file contents:")
        print(get_file_contents(udev_path))
