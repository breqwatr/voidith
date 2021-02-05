""" Library for RHEL migration operations """
import os
from pathlib import Path
from voithos.lib.migrate.linux_worker import LinuxWorker
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


class RhelWorker(LinuxWorker):
    """ Operate on mounted RedHat systems """

    def __init__(self, devices=None):
        """Operate on mounted RedHat systems
        Accepts a collection of devices to operate upon
        """
        debug(f"Initiating RhelWorker with devices: {devices}")
        super().__init__(devices=devices)

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

    def set_interface(
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
        """ Deploy a RHEL styled interface file """
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
