""" VMware command lib """
import os
import ssl
from pyVim import connect
from voithos.lib.system import error


ENV_VARS = ["VMWARE_USERNAME", "VMWARE_PASSWORD", "VMWARE_IP_ADDR"]
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
