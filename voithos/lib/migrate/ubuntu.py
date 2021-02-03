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
