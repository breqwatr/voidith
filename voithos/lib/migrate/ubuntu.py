""" Library for Ubuntu migration operations """
import os
from pathlib import Path
from ipaddress import IPv4Interface

from voithos.lib.system import error, is_mounted, debug, get_file_contents, grep
from voithos.lib.migrate.linux_worker import LinuxWorker


class UbuntuWorker(LinuxWorker):
    """ Operate on mounted RedHat systems """

    def __init__(self, devices=None):
        """Operate on mounted RedHat systems
        Accepts a collection of devices to operate upon
        """
        super().__init__(devices=devices)
        debug(f"Initiating UbuntuWorker with devices: {devices}")

    def uninstall(self, package, like=False):
        """ Uninstall packages from the given system """
        if not like:
            print(f"Uninstalling: {package}")
            self.chroot_run(f"dpkg --purge {package}")
            return
        dpkg_lines = self.chroot_run("dpkg -l")
        like_lines = [line for line in dpkg_lines if package in line]
        if not like_lines:
            print(f'No packages were found matching "{package}"')
            return
        for line in like_lines:
            pkg = [elem for elem in line.split(" ") if elem][1]
            print(f"Uninstalling: {pkg}")
            self.chroot_run(f"dpkg --purge {pkg}")

    def set_ifupdown_interface(
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
        """ Deploy an ifupdown styled interface file """
        debug("Setting ifupdown file")
        path = f"{self.ROOT_MOUNT}/etc/network/interfaces"
        interfaces_contents = get_file_contents(path)
        if interface_name in interfaces_contents:
            error(f"ERROR: {interface_name} is already in {path} - cannot continue", exit=True)
        self.debug_action(action=f"SET IFUPDOWN FILE: {path}")
        mode = "dhcp" if is_dhcp else "static"
        iface_lines = [
            f"auto {interface_name}",
            f"iface {interface_name} inet {mode}"
        ]
        if ip_addr and prefix:
            iface_lines.append(f"   address {ip_addr}")
            ip_obj = IPv4Interface(f"{ip_addr}/{prefix}")
            iface_lines.append(f"   netmask {ip_obj.netmask}")
        if gateway:
            iface_lines.append(f"   gateway {gateway}")
        if dns:
            nameservers = " ".join(dns)
            iface_lines.append(f"   dns-nameservers {nameservers}")
        if domain:
            iface_lines.append(f"   dns-search {domain}")
        print(f"Writing: {path}")
        with open(path, "a+") as iface_file:
            iface_file.write("\n")
            for line in iface_lines:
                iface_file.write(line+ "\n")
        with open(path, "r") as iface_file:
            print(iface_file.read())
        self.debug_action(end=True)

    def set_netplan_interface(
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
        """ Deploy a netplan styled interface file """
        netplan_dir_path = f"{self.ROOT_MOUNT}/etc/netplan"
        netplan_file_path = f"{netplan_dir_path}/{interface_name}.yaml"
        self.debug_action(action=f"SET NETPLAN FILE: {netplan_file_path}")
        # check the yaml files in the netplan dir to see if this interface is already defined
        dir_files = os.listdir(netplan_dir_path)
        yaml_files = [fil for fil in dir_files if fil.endswith(".yaml") ]
        # make sure this interface is not defined elsewhere
        for filename in yaml_files:
            file_path = f"{netplan_dir_path}/{filename}"
            debug(f"Ensuring {interface_name} is not in {file_path}")
            if f"{interface_name}:" in get_file_contents(file_path):
                error(f"ERROR: {interface_name} found in {file_path}", exit=True)
        # write the new yaml file
        iface_lines = [
            f"network:",
            f"  ethernets:",
            f"    {interface_name}:"
        ]
        if ip_addr and prefix:
            iface_lines.append(f"      dhcp4: no")
            iface_lines.append(f"      addresses: [\"{ip_addr}/{prefix}\"]")
            if gateway:
                iface_lines.append(f"      gateway4: {gateway}")
            if dns:
                nameservers = ', '.join('"{0}"'.format(entry) for entry in dns)
                iface_lines.append(f"      nameservers:")
                iface_lines.append(f"        addresses: [{nameservers}]")
                if domain:
                    iface_lines.append(f"        search: [\"{domain}\"]")
        elif is_dhcp:
            iface_lines.append(f"      dhcp4: yes")
        with open(netplan_file_path, "a+") as iface_file:
            for line in iface_lines:
                iface_file.write(line+ "\n")
        print(f"# {netplan_file_path}")
        with open(netplan_file_path, "r") as iface_file:
            print(iface_file.read())
        self.debug_action(end=True)

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
        """ Find the interface type (netplan/ifupdown) then deploy the file """
        if not is_mounted(self.ROOT_MOUNT):
            error(f"ERROR: Cannot set interface file, {self.ROOT_MOUNT} is not mounted", exit=True)
        if Path(f"{self.ROOT_MOUNT}/etc/netplan").exists():
            # This is (probably) a newer Ubuntu OS that uses Netplan
            debug("Using Netplan")
            self.set_netplan_interface(
                interface_name,
                is_dhcp,
                mac_addr,
                ip_addr=ip_addr,
                prefix=prefix,
                gateway=gateway,
                dns=dns,
                domain=domain
            )
        else:
            # This is (probably) an older Ubuntu OS that uses ifupdown
            self.set_ifupdown_interface(
                interface_name,
                is_dhcp,
                mac_addr,
                ip_addr=ip_addr,
                prefix=prefix,
                gateway=gateway,
                dns=dns,
                domain=domain
            )

