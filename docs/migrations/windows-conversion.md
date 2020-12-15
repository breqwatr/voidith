[Back to the migration guide](/vmware-migration.html)


# Converting Windows (10/2016/2019) VMs from VMware to OpenStack

## Requirements


Before this guide can be followed:

 - The virtual volumes of the VM must have already been imported into Cinder
   If that hasn't been done yet, follow [this guide](/vmware-migration.html) first.
 - The Windows migration worker VM must be online.
 - The OpenStack Neutron ports that this VM will use have been created.
   Their MAC addresses will be used to configure the VM's interface files.
 - A Windows migration worker is of equal or newer version (2012, 2016, 2019, etc) to the migration
   target VM.
 - The Windows migration worker has been configured with the Voithos powershell module.
   Follow [this guide](/migrations/windows-worker.html) to set up the Windows worker.



## Attach Cinder volumes to Windows worker

```bash
openstack server remove volume <server> <server>
openstack server add volume <server volume>
```

Assuming the Linux worker's server name is `linux-worker`,the Windows server's name is
`win-worker`, and the migration target VM's name is `Win2019-MigrateMe`, the commands would look
as follows:

```bash
# Example (with 2 volumes):
openstack server remove volume linux-worker Win2019-MigrateMe-1.vmdk
openstack server remove volume linux-worker Win2019-MigrateMe-0.vmdk
openstack server add volume windows-worker Win2019-MigrateMe-0.vmdk
openstack server add volume win-worker Win2019-MigrateMe-0.vmdk
openstack server add volume win-worker Win2019-MigrateMe-1.vmdk
```


## Convert the VM

Open the run window and execute `diskmgmt.msc`.
Ensure that the disks to be converted are un the offline state.

Open Powershell as an administrator.

```ps1

# Import the Voithos PS module
Import-Module Voithos

# Find the disks and Online them
$offDisks = Get-Disk | Where-Object OperationalStatus -eq "Offline"
$offDisks | Set-Disk -isOffline $False
$offDisks | Set-Disk -isReadOnly $False

# Determine the boot partition
$bootPartition = Get-TargetBootPartition

# Inject KVM drivers - Distro options: ["w7", "w8", "w8.1", "2k12", "2k12r2", "2k16", "2k19"]
Add-VirtioDrivers -Distro 2k19 $bootPartition

# Show the drivers
Get-PartitionDrivers $bootPartition

# Remove VMware Tools
Remove-VMwareTools $bootPartition


# Check if the boot type is UEFI or BIOS
Get-BootStyle $bootPartition

# Offline the disks
$offDisks | Set-Disk -isOffline $True

# Repair the offline disks
Repair-OfflineDisks
```


## Remove OpenStack Cinder volumes

```bash
openstack server remove volume <windows migration server> <volume>
```

Optionally, if `Get-BootStyle` returned `UEFI`, don't forget to enable UEFI boot:

```bash
openstack volume set --image-property hw_firmware_type=uefi <volume>
```
