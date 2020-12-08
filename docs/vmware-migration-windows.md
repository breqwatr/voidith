# Migrating Windows from VMware to OpenStack

## Requirements

Before this guide can be followed:

 - The virtual volumes of the VM must have already been imported into Cinder.
   If that hasn't been done yet, follow [this guide](/vmware-migration.html) first.
 - A Linux migration worker VM must be online and have the newly imported cinder volumes attached.
 - A Windows migration worker of equal or newer version (2012, 2016, 2019, etc) must be online and
   have the cinder volumes attached to it


These steps involve executing powershell scripts. These scripts run on your migration worker.
If you like, you can save them as .ps1 files and modify your execution policy to run them.

---



## Inject the VirtIO drivers

On the Windows migration worker, open PowerShell as an administrator. Paste this script into the
terminal window.

Note that the line `$distro="2k19"` is only accurate for Windows 2019. If you're migrating an older
server or windows client, change it as needed. You can find the valid options in the virtio disk
once it's been mounted. The common ones are `2k16`, `2k12R2`, `w10`, and `w8.1`.

```ps1

# Mount the VirtIO drivers ISO
$virtio_iso_path = "C:\virtio.iso"
$iso_exists = Test-Path $virtio_iso_path
if (!$iso_exists){
  Write-Host "ISO file not found - downloading to $virtio_iso_path"
  $iso_url = "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso"
  Invoke-WebRequest -Uri $iso_url -OutFile $virtio_iso_path
}
$virtio_vol = $(Get-Volume | Where-Object DriveType -eq "CD-ROM").DriveLetter
if (! $virtio_vol){
  Mount-DiskImage $virtio_iso_path
  $virtio_vol = $(Get-Volume | Where-Object DriveType -eq "CD-ROM"| Select-Object -last 1).DriveLetter
}
Write-Host "Mounted virtio-volume: $virtio_vol"


# Online all the disks
$off_disks = Get-Disk | Where-Object OperationalStatus -eq "Offline"
$off_disks | Set-Disk -IsOffline $False
# Turn off ReadOnly
$off_disks | Set-Disk -IsReadonly $False

# Collect the volumes that aren't C or virtio. They'll be the target ones we're migrating
$vols =  Get-Volume | Where-Object {$_.DriveLetter -ne $null -and $_.DriveLetter -ne "C" -and $_.DriveType -ne "CD-ROM"}


# While we're here, its a good time to chkdisk these volumes
$vols | Repair-Volume


# Find the boot vol, it has :\Windows\System32 in it.
$boot_vol = $vols | Foreach-object {
  $letter = $_.DriveLetter
  $sys32_path = $letter + ":/Windows/System32"
  $is_boot_vol = Test-Path $sys32_path
  if ($is_boot_vol){
    return ($letter+":\")
  }
}
Write-Host "Detected target boot volume: $boot_vol"


# Install the drivers to the boot vol
# Valid $distro values: "w7", "w8", "w8.1", "2k12", "2k12r2", "2k16", "2k19"
$distro="2k19"
$drivers = Get-ChildItem $virtio_vol":\" -Recurse | Where-Object {$_.PSIsContainer -eq $true -and $_.Name -eq "amd64" -and $_.Parent.Name -eq $distro}
$drivers | ForEach-Object {
  $driver = $_.FullName
  Write-Host "DISM /Image:$boot_vol /Add-Driver /Driver:$driver /Recurse /ForceUnsigned"
  DISM /Image:$boot_vol /Add-Driver /Driver:$driver /Recurse /ForceUnsigned
}


```

To verify, show the drivers.
The new drivers will all say Red Hat, though they're for Windows. This is expected.

```ps1
DISM /image:$boot_vol /Get-Drivers
```


---


## Remove VMware tools

Since Windows doesn't have any equivalent to Linux's `chroot` to leverage the VMware uninstaller,
you need to manually remove the registry keys and installed files. Paste this script into an
administrative Powershell prompt to clean it up.

```ps1
 # Reference: https://kb.vmware.com/s/article/1001354
# Windows 10, Windows 2016 and Windows 2019 Virtual Machine - Note the vmware ID they use is invalid
# Assumption: $boot_vol is already set from the driver import procedure. Format: "E:\"


# Load the HKLM\SOFTWARE\ registry hive
$hklm_software_path = "$boot_vol\Windows\System32\Config\SOFTWARE"
$HKEY_LOCAL_MACHINE_SOFTWARE = "HKLM\TEMPSOFTWARE"
Write-Host REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklm_software_path
REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklm_software_path

# Load the HKLM\SYSTEM\ registry hive
$hklm_system_path = "$boot_vol\Windows\System32\Config\SYSTEM"
$HKEY_LOCAL_MACHINE_SYSTEM = "HKLM\TEMPSYSTEM"
Write-Host REG LOAD $HKEY_LOCAL_MACHINE_SYSTEM $hklm_system_path
REG LOAD $HKEY_LOCAL_MACHINE_SYSTEM $hklm_system_path


# Find the key for VMWare Tools, if it's installed, call it $vmware_id
$has_vmware_tools = $False
$products_dir_path = ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Classes\Installer\Products\")
$product_paths = REG QUERY $products_dir_path
ForEach($product_path in $product_paths) {
  # skip leading blank line
  if ("$product_path" -eq ""){ continue }
  # If this $product_path is VMware, it has a ProductName that says so
  $product_name = REG QUERY $product_path /v ProductName 2> $null
  # skip this entry if $product_path has no ProductName
  if (!$?){ continue }
  # REG QUERY value output is multi-line. Find if any line says "VMware Tools"
  ForEach($line in $product_name){
    if ($line -like "*VMware Tools"){
      $has_vmware_tools = $True
      $vmware_id = $product_path.Split("\") | Select-Object -Last 1
    }
  }
}

# Now that we know it's installed and have the ID, clean up those entries
if ($has_vmware_tools){
  $keys = @(
    ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Classes\Installer\Features\" + $vmware_id),
    ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Classes\Installer\Products\" + $vmware_id),
    ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Microsoft\Windows\CurrentVersion\Installer\UserData\S-1-5-18\Products\" + $vmware_id),
    ($HKEY_LOCAL_MACHINE_SOFTWARE + "\VMware, Inc.")
  )
  ForEach($key in $keys){
    REG QUERY "`"$key`"" > $null 2> $null
    if (!$?){
      Write-Host "Failed to delete (not found): $key"
      continue
    }
    Write-Host REG DELETE "`"$key`"" /f
    REG DELETE "`"$key`"" /f
  }

  # Find the Uninstall key - it has its own identifier - and delete it
  $ui_paths = REG QUERY ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Microsoft\Windows\CurrentVersion\Uninstall")
  $removed_ui_key = $False
  ForEach ($ui_path in $ui_paths){
    if ("$ui_path" -eq "") { continue }
    $display_name = REG QUERY $ui_path /v DisplayName 2> $null
    if (!$?){ continue }
    ForEach($line in $display_name){
      if ($line -like "*VMware Tools"){
        Write-Host REG DELETE "`"$ui_path`"" /f
        REG DELETE "`"$ui_path`"" /f
        $removed_ui_key = $True
        break
      }
    }
    if ($removed_ui_key){ break }
  }
} # /end if has_vmware_tools



# Remove the service registry keys
# Since we can't use CurrentControlSet, loop through each ControlSet
$control_set_paths = REG QUERY $HKEY_LOCAL_MACHINE_SYSTEM | where {$_ -like "*ControlSet*"}
$services = @("VMTools", "vm3dservice", "vmvss", "VGAuthService")
ForEach ($control_set_path in $control_set_paths){
  ForEach ($service in $services){
    $service_key = ($control_set_path + "\Services\" + $service)
    REG QUERY $service_key > $null 2> $null
    if ($?){
        Write-Host REG DELETE $service_key /f
        REG DELETE $service_key /f
    }
  }
}

# Unload the hives
Write-Host REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE
REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE

Write-Host REG UNLOAD $HKEY_LOCAL_MACHINE_SYSTEM
REG UNLOAD $HKEY_LOCAL_MACHINE_SYSTEM


# Remove the VMware Tools installation directory
$folders = @(
  ($boot_vol + "Program Files\VMware"),
  ($boot_vol + "Program Files (x86)\VMware")
)
ForEach($folder in $folders){
  if ($(Test-Path $folder)){
    Write-Host Remove-Item -Recurse -Force $folder
    Remove-Item -Recurse -Force $folder
  }
}

```

---
## Clean-Up


Offline the disks so they're safe to remove with `openstack server remove volume`.
The `$off_disks` variable  was set during the driver installation. If you've lost the variable,
open the Disk# Management tool and manually offline the disks.

```ps1
$off_disks | Set-Disk -IsOffline $True
```







