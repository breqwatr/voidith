[Back to the migration guide](/vmware-migration.html)


# Converting Windows (10/2012/2016/2019) VMs from VMware to OpenStack

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
openstack server add volume win-worker Win2019-MigrateMe-0.vmdk
openstack server add volume win-worker Win2019-MigrateMe-1.vmdk
```


## Convert the VM

Open the run window and execute `diskmgmt.msc`.
Ensure that the disks to be converted are in the offline state.

Open PowerShell as an administrator:

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
# You will be prompted to confirm that the provided value is correct. Enter "y" to continue.
Add-VirtioDrivers -Distro $distro -BootPartition $bootPartition

# Show the drivers
Get-PartitionDrivers -BootPartition $bootPartition

# Remove VMware Tools
Remove-VMwareTools -BootPartition $bootPartition

# Check if the boot type is UEFI or BIOS
Get-BootStyle -BootPartition $bootPartition
```


---


# (Optional) Inject a Startup script for Static IPs & Online Disks


Servers with multiple data volumes may need a GPO startup script to initialize those disks on boot.
Windows server 2012 will always require this.

If the server is being migrated but keeping its IP addresses, another issue will occur where the IP
address of the migrating VM is lost. The virtual NIC assigned to the VM changes, so Windows makes
a new interface.

This process will:

1. Deploy the Voithos PS module into the migration target
1. Create a Powershell script to online the disks / set the static IPs of the new NICs
1. Back up the current GPO settings
1. Set the GPO startup script in the migration target

Each of these commands requires the `Voithos` module to be loaded.

## Deploy Voithos PS module to Migration Target VM

On the Windows migration worker's Powershell session:

```ps1
Copy-VoithosModuleToBootPartition -BootPartition $bootPartition
```

## Create Ports for Static IP addresses

In neutron, create the ports for the VM. Note the IP and MAC of the ones that don't use DHCP.
It can be helpful to include the server name in the port name.

**NOTE**: Make sure you're sourced to the project where the VM will be created

```bash
openstack port create --network <network> --fixed-ip subnet=<subnet>,ip-address=<IP address>  <port name>
```

The `port create` command will print a table including a `mac_address` value for the new port.
This will be used by the RunOnce script to identify the correct interface when setting the IP.

When creating the server, use `openstack server create --nic port-id=<id>` to select this port.


## Create the RunOnce script

Back up the current GPO settings, as they'll get overwritten when we set the one ones.

```ps1
Backup-MountedGPOSettings -BootPartition $bootPartition
```

The `New-RunOnceScript` command will create a new script file
`C:\Windows\System32\GroupPolicy\Machine\Scripts\Startup\startup.ps1`
on the migration target and open a Notepad window to edit it.

```ps1
# When prompted by Notepad if you want to create a new file, say yes
New-StartupScript -BootPartition $bootPartition
```

Inside this Notepad file, a script must be written. Here are some examples. The clean-up
steps are optional, but help to leave the system pristine.

```ps1
try{
  Unblock-File "C:\Windows\System32\WindowsPowerShell\v1.0\Modules\Voithos\voithos.psm1"
} catch {
  Write-Host "WARNING: Unblock-file failed"
}
Import-Module Voithos

# Set the extra disks to online on boot
Set-AllDisksOnline


# (Optional) Set the interface on boot
# Primary interface with Gateway and DNS settings included
Set-InterfaceAddress `
  -MacAddress "aa:bb:cc:dd:ee" `
  -IPAddress "1.2.3.4" `
  -SubnetPrefix 24 `
  -GatewayIPAddress "1.2.3.1" `
  -DNSAddressCSV "1.1.1.1,8.8.8.8"

# Secondary interface with no gateway/DNS
Set-InterfaceAddress -MacAddress "aa:bb:cc:dd:ee" -IPAddress "1.2.3.4" -SubnetPrefix 24


# Clean-up to restore the VM to the pre-migration state
# Remove the GPO config and restore the backed up one
Reset-GPOConfig

# Remove the Voithos PowerShell module
Remove-Module Voithos
Remove-Item -Recurse -Force -Confirm:$False -ErrorAction Ignore "C:\Windows\System32\WindowsPowerShell\v1.0\Modules\Voithos"


# Remove the directory the GPOs got backed up to
Remove-Item -Recurse -Force -Confirm:$False -ErrorAction Ignore C:\Breqwatr

# Reboot to apply the old startup GPOs
shutdown /r /t 0
```

Save and close the file in Notepad.


## Set the local GPO startup script

```ps1
Set-MountedGPOStartupScript -BootPartition $bootPartition
```

---


# Clean Up

Offline the disks and try to repair them in case there's any corruption. If you've lost the value
of `$offDisks` you can manually offline the disks from the Disk Management tool.

```ps1
$offDisks | Set-Disk -isOffline $True

# Repair the offline disks
Repair-OfflineDisks
```


---


# Remove OpenStack Cinder volumes

Once the conversion is finished, remove the volumes from the Windows worker:

```bash
openstack server remove volume <windows migration server> <volume>
```

Optionally, if `Get-BootStyle` returned `UEFI`, don't forget to enable UEFI boot:

```bash
openstack volume set --image-property hw_firmware_type=uefi <volume>
```
