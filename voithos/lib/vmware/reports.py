""" Generate reports from VMWare VM data """
from pyVmomi import vim


def bytes_to_gb(bytes_val):
    """ Convert bytes to GB, rounded to 2 decimal places """
    BYTES_IN_GB = 1024 * 1024 * 1024
    gbytes = bytes_val / BYTES_IN_GB
    return round(gbytes, 2)


def get_disk_data(vm):
    """ Return a list of dictionaries showing useful disk-related data """
    disk_data = []
    for dev in vm.config.hardware.device:
        if not isinstance(dev, vim.vm.device.VirtualDisk):
            continue
        shared = dev.backing.sharing != "sharingNone"
        disk_data.append(
            {
                "label": dev.deviceInfo.label,
                "uuid": dev.backing.uuid,
                "thin_provisioned": dev.backing.thinProvisioned,
                "shared": shared,
                "capacity_gb": bytes_to_gb(dev.capacityInBytes),
            }
        )
    return disk_data


def get_partition_data(vm):
    """ Return a dictionary of this VMs available useful partition data """
    partitions = vm.guest.disk
    total_used_gb = 0
    part_data = []
    for part in partitions:
        used_bytes = part.capacity - part.freeSpace
        used_gb = bytes_to_gb(used_bytes)
        part_data.append(
            {
                "path": part.diskPath,
                "capacity_bytes": part.capacity,
                "capacity_gb": bytes_to_gb(part.capacity),
                "free_bytes": part.freeSpace,
                "free_gb": bytes_to_gb(part.freeSpace),
                "used_bytes": used_bytes,
                "used_gb": used_gb,
            }
        )
        total_used_gb += used_gb
    return {"total_used_gb": total_used_gb, "paritions": part_data}


def get_network_data(vm):
    """ return a list of dictionaries showing useful network data """
    net_data = []
    for dev in vm.config.hardware.device:
        if not hasattr(dev, "macAddress"):
            continue
        pci_slot_num = dev.slotInfo.pciSlotNumber if dev.slotInfo is not None else ""
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
    """ Return a dictionary of useful data about an entire VM """
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
            "partitions": get_partition_data(vm),
            "disks": get_disk_data(vm),
        },
        "network": {
            "num_interfaces": vm.summary.config.numEthernetCards,
            "networks": get_network_data(vm),
        },
    }
