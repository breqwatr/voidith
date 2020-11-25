""" VMware command lib """
import os
import ssl
import requests
from datetime import datetime
from time import time
from pathlib import Path

from hurry.filesize import size
from pyVim import connect
from pyVmomi import vim

from voithos.lib.system import error


ENV_VARS = ["VMWARE_USERNAME", "VMWARE_PASSWORD", "VMWARE_IP_ADDR"]
EXPORT_HEADERS = {"Accept": "application/x-vnd.vmware-streamVmdk"}
BYTES_IN_GB = 1024 * 1024 * 1024


def assert_env_vars():
    """ Fail if environment variables aren't here """
    failed = False
    for env_var in ENV_VARS:
        if env_var not in os.environ:
            error(f"Required environment variable is not defined: {env_var}", exit=False)
            failed = True
    if failed:
        error("Cannot continue until all environment variables are set", exit=True)


def get_connection():
    """ Return a SmartConnect instance to VMWare, handle cert problems """
    assert_env_vars()
    username = os.environ["VMWARE_USERNAME"]
    password = os.environ["VMWARE_PASSWORD"]
    ip_addr = os.environ["VMWARE_IP_ADDR"]
    try:
        conn = connect.SmartConnect(host=ip_addr, user=username, pwd=password)
    except ssl.SSLCertVerificationError:
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            ctx.verify_mode = ssl.CERT_NONE
            conn = connect.SmartConnect(host=ip_addr, user=username, pwd=password, sslContext=ctx)
        except ssl.SSLEOFError:
            conn = connect.SmartConnectNoSSL(host=ip_addr, user=username, pwd=password)
    return conn


def get_vms(conn, index=0):
    """ Return a list (ManagedObject) of VMs in the indexed datacenter (usually 0) """
    datacenter = conn.content.rootFolder.childEntity[index]
    return datacenter.vmFolder.childEntity


def get_disks(vm):
    """ Return a list of dicts showing disks in this VM """
    disk_data = []
    for dev in vm.config.hardware.device:
        if "Disk" not in str(type(dev)):
            continue
        capacity_gb = dev.capacityInBytes / BYTES_IN_GB
        shared = dev.backing.sharing != "sharingNone"
        disk_data.append(
            {
                "label": dev.deviceInfo.label,
                "uuid": dev.backing.uuid,
                "thin_provisioned": dev.backing.thinProvisioned,
                "shared": shared,
                "capacity_gb": capacity_gb,
            }
        )
    return disk_data


def get_partitions(vm):
    """ Return a dict showing partitions in this VM """
    partitions = vm.guest.disk
    total_used_gb = 0
    part_data = []
    for part in partitions:
        used_bytes = part.capacity - part.freeSpace
        used_gb = round((used_bytes / BYTES_IN_GB), 2)
        capacity_gb = round((part.capacity / BYTES_IN_GB), 2)
        free_gb = round((part.freeSpace / BYTES_IN_GB), 2)
        part_data.append(
            {
                "path": part.diskPath,
                "capacity_bytes": part.capacity,
                "capacity_gb": capacity_gb,
                "free_bytes": part.freeSpace,
                "free_gb": free_gb,
                "used_bytes" "used_gb": used_gb,
            }
        )
        total_used_gb += used_gb
    return {"total_used_gb": total_used_gb, "paritions": part_data}


def get_networks(vm):
    """ return list of dicts with network interface and vswitch configurations """
    net_data = []
    for dev in vm.config.hardware.device:
        if not hasattr(dev, "macAddress"):
            continue
        pci_slot_num = dev.slotInfo.pciSlotNumber if dev.slotInfo != None else ""
        net_data.append(
            {
                "label": dev.deviceInfo.label,
                "nic_type": type(dev).__name__,
                "vswitch_name": dev.backing.deviceName,
                "connected": dev.connectable.connected,
                "pci_slot_num": pci_slot_num,
            }
        )
    return net_data


def get_vm_data(vm):
    """ Return a dictionary of useful data about this VM """
    return {
        "name": vm.name,
        "uuid": vm.summary.config.uuid,
        "create_date": str(vm.config.createDate),
        "guest_os": vm.summary.config.guestFullName,
        "uptime_seconds": vm.summary.quickStats.uptimeSeconds,
        "status": vm.summary.overallStatus,
        "num_cpu": vm.summary.config.numCpu,
        "ram": {
            "total_mb": vm.summary.config.memorySizeMB,
            "used_mb": vm.summary.config.memorySizeMB,
        },
        "storage": {
            "num_disks": vm.summary.config.numVirtualDisks,
            "partitions": get_partitions(vm),
            "disks": get_disks(vm),
        },
        "network": {
            "num_interfaces": vm.summary.config.numEthernetCards,
            "networks": get_networks(vm),
        },
    }


def filter_vms(names):
    """Return a filtered list of VM data by name
    Using * in any element will cause them all to be returned

    This is a top-level function that handles its own connections, to be used by the CLI
    """
    conn = get_connection()
    vms = get_vms(conn)
    vm_data = []
    if "*" in names:
        filtered_list = vms
    else:
        filtered_list = list(vm for vm in vms if any(name in vm.name for name in names))
    for vm in filtered_list:
        vm_data.append(get_vm_data(vm))
    connect.Disconnect(conn)
    return vm_data


def get_vm_by_uuid(uuid, conn):
    """ Return a VM with a given UUID """
    vms = get_vms(conn)
    vm = next((vm for vm in vms if vm.config.uuid == uuid), None)
    if vm is None:
        error("Failed to find a VM with that UUID", exit=True)
    return vm


def print_vm_size(vm):
    """Print the size of a VM's disks, in total
    Can't seen to find exact disk sizes during downloads
    """
    print(f"Storage for {vm.name}:")
    unshared = size(vm.summary.storage.unshared)
    print(f"  Total unshared disk size: {unshared}")
    for dev in vm.config.hardware.device:
        if "Disk" not in str(type(dev)):
            continue
        capacity = size(dev.capacityInBytes)
        print(f"  {dev.deviceInfo.label}: {capacity}")


def assert_offline(vm):
    """ make sure VM is off """
    if vm.runtime.powerState != vim.VirtualMachine.PowerState.poweredOff:
        error("VM is not powered off - quitting", exit=True)


def get_ready_nfc_lease(vm):
    """ Get an NFC lease (export the vm), wait until its ready to use before returning it """
    nfc_lease = vm.ExportVm()
    # Wait for the NFC lease to be ready
    max_nfc_retries = 60
    for attempt in range(1, (max_nfc_retries + 1)):
        if nfc_lease.state == vim.HttpNfcLease.State.ready:
            break
        if attempt == (max_nfc_retries - 1):
            raise (f"ERROR - NFC lease state {nfc_lease.state} after {max_nfc_retries} retries")
        sleep(1)
    return nfc_lease


def get_export_disk_devices(nfc_lease):
    """ Return the devices that can be saved """
    # Export device URL objects have filenames but not UUIDs so we have to download all at once
    # Only count devices that can be downloaded (targetId) and are not ISO files (dev.disk)
    return list(dev for dev in nfc_lease.info.deviceUrl if dev.targetId and dev.disk)


def get_export_cookies(conn):
    """ Create a cookie for the HTTP export requests """
    stub = conn._stub.cookie
    stub_list = stub.split(";")
    vmware_soap_session = stub_list[0].split("=")[1]
    path = stub_list[1].lstrip()
    return {"vmware_soap_session": f"{vmware_soap_session}; ${path}"}


def _save_block(block, vol_file):
    """ Save and commit a block of an HTTP response body to disk. """
    if not block:
        return
    vol_file.write(block)
    vol_file.flush()
    os.fsync(vol_file.fileno())


class ProgressTracker:
    """ Track the progress of the download"""

    def __init__(self):
        self.last_show = time()
        self.last_bytes = 0
        self.bytes = 0
        self.old_bytes = 0
        self.interval_seconds = 15
        self.start_ts = 0

    def show(self):
        now = time()
        if self.start_ts == 0:
            self.start_ts = now
        if now <= (self.last_show + self.interval_seconds):
            return
        interval = int(now - self.last_show)
        self.last_show = now
        progress = size(self.bytes)
        # Larger chunk sizes can take longer than the interval.seconds, skewing math
        # avoid dividing by 0 when calculating rates
        total_divisor = now - self.start_ts
        total_divisor = total_divisor if total_divisor else 1
        interval_divisor = interval if interval else 1
        total_rate = size(self.bytes / total_divisor)
        interval_rate = size((self.bytes - self.old_bytes) / interval_divisor)
        self.old_bytes = self.bytes
        print(
            str(datetime.now(tz=None)) + f" - Progress: {progress}"
            f" - Total rate: {total_rate}/s"
            f" - Rate of last {interval}s: {interval_rate}/s"
        )


def download_device(dev, cookies, base_dir, chunk_size_mb=20):
    """ Download the given device to base_dir, printing progress along the way """
    path = os.path.join(base_dir, dev.targetId)
    progress_tracker = ProgressTracker()
    with open(path, "wb") as vol_file:
        # The dev.url value is https:/*/ for some reason, replace it with the IP
        ip_addr = os.environ["VMWARE_IP_ADDR"]
        url = dev.url.replace("*/", f"{ip_addr}/")
        print(f"Downloading {url} to {path}")
        resp = requests.get(url, stream=True, headers=EXPORT_HEADERS, cookies=cookies, verify=False)
        if not resp.ok:
            resp.raise_for_status()
        mb_in_bytes = 1024 * 1024
        for block in resp.iter_content(chunk_size=(chunk_size_mb * mb_in_bytes)):
            _save_block(block, vol_file)
            progress_tracker.bytes += len(block)
            progress_tracker.show()


def download_vm(uuid, dest_dir):
    """Download the volumes of a VM to the given destination directory

    This is a top-level function used by the CLI and handles its own connections
    """
    # Get abspath and ensure dest dir exists
    dir_path = Path(dest_dir)
    if not dir_path.is_dir():
        error(f"Directory {dest_dir} must exist", exit=True)
    base_dir = str(dir_path.absolute())
    # Connect to VMWare and find the VM
    conn = get_connection()
    vm = get_vm_by_uuid(uuid, conn)
    print_vm_size(vm)
    # Create an Export in VMWare for the VM, allowing its volumes to be downloaded
    nfc_lease = get_ready_nfc_lease(vm)
    cookies = get_export_cookies(vm)
    # Download each volume to the given dest_dir
    devices = get_export_disk_devices(nfc_lease)
    for dev in devices:
        download_device(dev, cookies, base_dir)
    # Clean up the connection
    connect.Disconnect(conn)
