""" Library for Ubuntu migration operations """
from voithos.lib.migrate.linux_worker import LinuxWorker
from voithos.lib.system import debug


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
