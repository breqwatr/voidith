""" Handle exporting a VMWare VM """
import os
import requests
import signal
import sys
from datetime import datetime
from time import sleep, time
from threading import Thread
from pathlib import Path

from hurry.filesize import size
from pyVmomi import vim

from voithos.lib.system import run


SLEEP_INTERVAL = 30  # seconds


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

    def download(self):
        """ Initiate the download process """
        downloads = []
        # Start a thread running WGET for each vmdk in parralel
        gb_total = bytes_to_gb(self.size_in_bytes)
        print(f"Download {gb_total} GB:")
        for dev in self.lease_disks:
            # Collect the download paths and filenames
            url = dev.url.replace("*/", f"{self.vmware_mgr.ip_addr}/")
            file_path = os.path.join(self.base_dir, dev.targetId)
            print(f"  {file_path} <-- {url}")
            thread = Thread(target=download_thread, kwargs={"url": url, "file_path": file_path})
            thread.start()
            downloads.append(
                {
                    "url": url,
                    "file_path": file_path,
                    "thread": thread,
                    "last_size": 0,
                    "size": 0,
                    "finished_size_thick": 0,
                    "finished_size_thin": 0,
                    "finshed_speed": 0,
                    "done": False,
                }
            )
        sleep(2)  # Give wget a second to get going
        print(f"  Starting download ... Progress updates every {SLEEP_INTERVAL} seconds")
        # Every x seconds, check the file sizes and provide a status update. Also update NFC lease
        num_downloading_files = len(downloads)
        elapsed_seconds = 0
        while num_downloading_files >= 1:
            # Count the alive threads, when the count is 0 this is the last iteration
            num_downloading_files = len([dld for dld in downloads if dld["thread"].is_alive()])
            if num_downloading_files == 0:
                break  # no need to wait 30 seconds at the end
            # wait 30 seconds (or whatever SLEEP_INTERVAL is) per check
            print("")
            sleep(SLEEP_INTERVAL)
            elapsed_seconds += SLEEP_INTERVAL
            print(f"Downloading files: {num_downloading_files}/{len(downloads)} remaining")
            downloaded_bytes_thick = 0  # re-calc'd each 30 seconds
            downloaded_bytes_thin = 0
            for download in downloads:
                if download["done"]:
                    # This VMDK download's download completion tasks have been done
                    # use its "thick size" instead
                    downloaded_bytes_thick += download["finished_size_thick"]
                    print_download_progress(download, download["finished_size_thick"])
                    downloaded_bytes_thin += download["finished_size_thin"]
                    continue
                if not download["thread"].is_alive():
                    # This download just finished, find its "finished size" and mark it done
                    download["done"] = True
                    download["finished_size_thick"] = get_vmdk_thick_size(download["file_path"])
                    downloaded_bytes_thick += download["finished_size_thick"]
                    download["finished_size_thin"] = Path(download["file_path"]).stat().st_size
                    downloaded_bytes_thin += download["finished_size_thin"]
                    download["finished_speed"] = round(
                        downloaded_bytes_thin / 1024 / 1024 / elapsed_seconds, 2
                    )
                    print_download_progress(download, download["finished_size_thick"])
                    continue
                # {download} is still downloading, find its current progress by checking file size
                file_size = Path(download["file_path"]).stat().st_size  # (thin size)
                downloaded_bytes_thick += file_size  # We don't know the real thick size yet
                downloaded_bytes_thin += file_size
                download["last_size"] = download["size"]
                download["size"] = file_size
                print_download_progress(download, file_size)  # use thin size for progress now
            self.percent_transfered = int(downloaded_bytes_thick / self.size_in_bytes * 100)
            self.lease.HttpNfcLeaseProgress(self.percent_transfered)
            gb_down_thick = bytes_to_gb(downloaded_bytes_thick)
            print(
                f"\- Total Downloaded: \t{gb_down_thick} GB / {gb_total} GB - {self.percent_transfered}%"
            )
            thick_avg_speed_mbs = round(downloaded_bytes_thick / 1024 / 1024 / elapsed_seconds, 2)
            print(f"\- Avg Speed (thick): \t{thick_avg_speed_mbs} MB/s")
            thin_avg_speed_mbs = round(downloaded_bytes_thin / 1024 / 1024 / elapsed_seconds, 2)
            print(f"\- Avg Speed (thin): \t{thin_avg_speed_mbs} MB/s")
        print("Finished download, closing NFC lease")
        self.lease.HttpNfcLeaseProgress(100)
        self.lease.HttpNfcLeaseComplete()

    def hold_nfc_lease(self):
        """ Open and hold an NFC lease until ctrl-c is passed """
        print("Opening and holding NFC lease - Ctrl+C to close lease")
        gb_total = bytes_to_gb(self.size_in_bytes)
        print(f"Size: {gb_total} GB")

        def signal_handler(sig, frame):
            print("You pressed Ctrl+C - Closing NFC lease...")
            self.lease.HttpNfcLeaseProgress(100)
            self.lease.HttpNfcLeaseComplete()
            print("Gracefully closed NFC lease")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        for dev in self.lease_disks:
            # Collect the download paths and filenames
            url = dev.url.replace("*/", f"{self.vmware_mgr.ip_addr}/")
            file_path = os.path.join(self.base_dir, dev.targetId)
            print(f"  {file_path} <-- {url}")
        while True:
            sleep(30)
            self.percent_transfered = 50
            self.lease.HttpNfcLeaseProgress(self.percent_transfered)
            now = str(datetime.fromtimestamp((time())))
            print(f"{now} - Renewed NFC lease")


def print_download_progress(download, progress):
    """ Print the progress of a download """
    # last interval speed
    # total speed
    # path
    if download["done"]:
        done = "(DONE)"
        speed = f"\t[AVG SPEED: {download['finished_speed']} MB/s]"
    else:
        done = ""
        diff = download["size"] - download["last_size"]
        current_speed = round(diff / 1024 / 1024 / SLEEP_INTERVAL, 2)
        speed = f"\t[CUR SPEED: {current_speed} MB/s]"
    size_gb = bytes_to_gb(progress)
    print(f"  {download['file_path']} - {size_gb} GB {speed} {done}")


def download_thread(url, file_path):
    """ Start a thread to download the file """
    run(f"wget --quiet --no-check-certificate {url} -O {file_path}")


def get_vmdk_thick_size(file_path):
    """ Execute qemu-img show inside a container, direct mapping the volume """
    name = "qemu-img-info"
    image = "breqwatr/qemu-img:latest"
    path = Path(file_path)
    file_abspath = path.absolute().__str__()
    run = f"qemu-img info {file_abspath}"
    mount = f"-v {vol_abspath}:{vol_abspath}"
    cmd = f"docker run --rm -it --name {name} {mount} {image} {run}"

    """ Return the 'thick' size of a VMDK file in bytes as an integer - requires qemu-utils """
    qemu_img_lines = run(f"cmd")
    vsize_line = next(line for line in qemu_img_lines if "virtual size" in line)
    size_bytes = int(vsize_line.split(" ")[-2].replace("(", ""))
    return size_bytes


def bytes_to_gb(qty_bytes):
    """ Return a GB value of bytes, rounded to 2 decimals """
    bytes_in_gb = 1024 * 1024 * 1024
    qty_gb = qty_bytes / bytes_in_gb
    return round(qty_gb, 2)
