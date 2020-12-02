""" Handle exporting a VMWare VM """
import os
import requests
from datetime import datetime
from time import sleep, time

from hurry.filesize import size
from pyVmomi import vim


class VMWareExportLeaseNotReady(Exception):
    """ After waiting some time, the NFC export lease did not become ready """


class VMWareOnlineVMCantMigrate(Exception):
    """ Online VMs cannot be migrated """


class VMWareExporter:
    """ Object used to wrangle VMWare exports """

    def __init__(self, vmware_mgr, vm, base_dir=None, interval=15):
        """ Construct the exporter around a VM """
        if vm.runtime.powerState != vim.VirtualMachine.PowerState.poweredOff:
            raise VMWareOnlineVMCantMigrate("ERROR: The VM is on. It must be offline")
        # progress tracking data
        self.start_ts = int(time())
        self.last_print = int(time())
        self.interval_seconds = interval
        self.last_transfered_bytes = 0
        self.transfered_bytes = 0
        # Download data
        self.vm = vm
        self.lease = None
        self.load_export_lease()
        self.base_dir = base_dir if base_dir is not None else os.getcwd()
        self.vmware_mgr = vmware_mgr
        self.chunk_size = 1024 * 1024 * 20  # 20 MB
        self.percent_transfered = 0

    @property
    def disks(self):
        """ Return the hardware devices that are actually disks """
        # Each disk's size can be found with dev.capacityInBytes
        return [
            device
            for device in self.vm.config.hardware.device
            if isinstance(device, vim.vm.device.VirtualDisk)
        ]

    @property
    def size_in_bytes(self):
        """ Return the total size of all unshared disks on this VM """
        size = 0
        for dev in self.vm.config.hardware.device:
            if not isinstance(dev, vim.vm.device.VirtualDisk):
                continue
            size += dev.capacityInBytes
        return size

    @property
    def lease_disks(self):
        """Return the disks presented by the export NFC lease

        Only count devices that can be downloaded (dev.targetId)
        and are not ISO files (dev.disk)
        """
        return [dev for dev in self.lease.info.deviceUrl if dev.targetId and dev.disk]

    @property
    def cookies(self):
        """ Return cookies to initiate the HTTP-based VMDK transfer request """
        stub = self.vmware_mgr.conn._stub.cookie
        stub_list = stub.split(";")
        vmware_soap_session = stub_list[0].split("=")[1]
        path = stub_list[1].lstrip()
        return {"vmware_soap_session": f"{vmware_soap_session}; ${path}"}

    def load_export_lease(self):
        """ Get an NFC lease (export the vm), wait until its ready to use before returning it """
        self.lease = self.vm.ExportVm()
        # Wait for the NFC lease to be ready
        max_retries = 60
        for attempt in range(1, (max_retries + 1)):
            if self.lease.state == vim.HttpNfcLease.State.ready:
                return
            sleep(1)
        raise VMWareExportLeaseNotReady(
            f"ERROR - NFC lease state {self.lease.state} after {max_retries} retries"
        )

    def print_progress(self, new_bytes_written):
        """ Increments the byte counter and handles printing progress """
        if self.interval_seconds <= 0:
            # progress tracking is disabled when interval is 0
            return
        self.transfered_bytes += new_bytes_written
        now = time()
        if now <= (self.last_print + self.interval_seconds):
            # Nothing to print, we've already printed during this interval
            return
        # Set interval because chunks can take longer than interval.seconds
        interval = int(now - self.last_print)
        self.last_print = now
        # avoid dividing by 0 when calculating rates - divisors are in seconds
        total_divisor = now - self.start_ts
        total_divisor = total_divisor if total_divisor else 1
        interval_divisor = interval if interval else 1
        # calculate and print the transfer rates - total and in the last interval
        total_rate = size(self.transfered_bytes / total_divisor)
        interval_bytes = self.transfered_bytes - self.last_transfered_bytes
        interval_rate = size(interval_bytes / interval_divisor)
        self.last_transfered_bytes = self.transfered_bytes
        self.percent_transfered = int(self.transfered_bytes / self.size_in_bytes * 100)
        print(
            str(datetime.now(tz=None)) + f" - Progress: {size(self.transfered_bytes)}"
            f" ({self.percent_transfered}%)"
            f" - Total rate: {total_rate}/s"
            f" - Rate of last {interval}s: {interval_rate}/s"
        )

    def download(self):
        """ Initiate the download process """
        print(f"Total VM Size: {size(self.size_in_bytes)}")
        for dev in self.lease_disks:
            file_path = os.path.join(self.base_dir, dev.targetId)
            with open(file_path, "wb") as vol_file:
                # The dev.url value is https:/*/ for some reason, replace it with the IP
                url = dev.url.replace("*/", f"{self.vmware_mgr.ip_addr}/")
                print(f"Downloading {url} to {file_path}")
                headers = {"Accept": "application/x-vnd.vmware-streamVmdk"}
                resp = requests.get(
                    url, stream=True, headers=headers, cookies=self.cookies, verify=False
                )
                for block in resp.iter_content(chunk_size=(self.chunk_size)):
                    if not block:
                        continue
                    vol_file.write(block)
                    # TO DO: Try swapping len(block) with self.chunk_size for speed
                    self.print_progress(len(block))
                    # update the export progress in VMWare
                    self.lease.HttpNfcLeaseProgress(self.percent_transfered)
        # when the loop is done, set the progress to 100% (to handle edge cases)
        self.lease.HttpNfcLeaseProgress(100)
        self.lease.HttpNfcLeaseComplete()
