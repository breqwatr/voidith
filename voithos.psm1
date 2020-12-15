# ps1
# This is the Voithos Powershell Module
# Save it to $PSHome\Modules\Voithos\ on a Windows system
# Import it with "Import-Module Voithos"
# These functions provide some useful Windows utilities, particularly for migrations


function Repair-OfflineDisks {
  # Run Repair-Volume against each lettered partition, on each offline disk
  Get-Disk | Where-Object OperationalStatus -eq "Offline"  | ForEach-Object {
    Write-Host ("Repairing Disk " + $_.Number)
    $_ | Set-Disk -isOffline $False
    $_ | Set-Disk -isReadOnly $False
    Get-Partition -DiskNumber $_.Number | Where-Object DriveLetter | Get-Volume | Repair-Volume
    $_ | Set-Disk -isOffline $True
  }
}


function Get-TargetBootPartition {
  # Get the target boot partition for migrating a VM - a Windows boot partition other than C:\
  # Return a Get-Partition entry (CimInstance)
  Get-Disk | Where-Object Number -ne 0 | ForEach-Object {
    $disk = $_
    # Set it online and loop through each of its partitions that have letters
    Get-Partition -DiskNumber $disk.Number | Where-Object DriveLetter | Foreach-Object {
      # Check if this drive letter is the boot volume
      $partition = $_
      $sys32 = $partition.DriveLetter + ":/Windows/System32"
      $isBootPartition = Test-Path $sys32
      if ($isBootPartition){
        return $partition
      }
    }
  }
}


function Save-VirtioISO {
  # Download the Virtio ISO file if its missing - Return the path to the file
  $path = "C:\virtio.iso"
  $exists = Test-Path $virtioIsoPath
  if (!$exists){
    Write-Host "ISO file not found - downloading to $path"
    $url = "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso"
    Invoke-WebRequest -Uri $url -OutFile $path
  }
  return $path
}


function Get-VirtioVolume {
  # Ensure the VirtIO file is downloaded and mounted - Return a Get-Volume (CimInstance) object
  $volume = Get-Volume | Where-Object DriveType -eq "CD-ROM" | Where-Object FileSystemLabel -like "virtio-win*"
  if ($volume){ return $volume }
  return Save-VirtioISO | Mount-DiskImage | Get-Volume
}


function Add-VirtioDrivers {
  param(
    [Parameter(Position = 0, ValueFromPipeline = $true, ValueFromRemainingArguments = $true)]
    [PSObject]$BootPartition,
    [string]$Distro
  )
  # Install all of the VirtIO drivers for the given OS using DISM on the selected BootPartition
  $virtio_drive = $(Get-VirtioVolume).DriveLetter + ":\"
  $drivers = Get-ChildItem  -Recurse $virtio_drive | Where-Object {
    $_.PSIsContainer -eq $true -and $_.Name -eq "amd64" -and $_.Parent.Name -eq $distro
  }
  $bootVol = $BootPartition.DriveLetter +":/"
  ForEach ($driver in $drivers){
    $driver_file = $driver.FullName
    Write-Host "DISM /Image:$bootVol /Add-Driver /Driver:$driver_file /Recurse /ForceUnsigned"
    DISM /Image:$bootVol /Add-Driver /Driver:$driver_file /Recurse /ForceUnsigned
  }
}


function Get-PartitionDrivers {
  param(
    [Parameter(Position = 0, ValueFromPipeline = $true, ValueFromRemainingArguments = $true)]
    [PSObject]$BootPartition
  )
  # Run DISM /Get-Drivers on the given partition
  $bootVol = $BootPartition.DriveLetter +":/"
  Write-Host "DISM /Image:$bootVol /Get-Drivers"
  DISM /Image:$bootVol /Get-Drivers
}


function Remove-VMwareTools {
  param(
    [Parameter(Position = 0, ValueFromPipeline = $true, ValueFromRemainingArguments = $true)]
    [PSObject]$BootPartition
  )
  # Manually remove all traces of VMware Tools, file-by-file and registry key-by-registry key
  $letter = $BootPartition.DriveLetter
  # Load the HKLM\SOFTWARE\ registry hive
  $hklmPath = ($letter + ":\Windows\System32\Config\SOFTWARE")
  $HKEY_LOCAL_MACHINE_SOFTWARE = "HKLM\TEMPSOFTWARE"
  Write-Host REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath
  REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath
  # Load the HKLM\SYSTEM\ registry hive
  $hklmSystemPath = ($letter + ":\Windows\System32\Config\SYSTEM")
  $HKEY_LOCAL_MACHINE_SYSTEM = "HKLM\TEMPSYSTEM"
  Write-Host REG LOAD $HKEY_LOCAL_MACHINE_SYSTEM $hklmSystemPath
  REG LOAD $HKEY_LOCAL_MACHINE_SYSTEM $hklmSystemPath
  # Find the key for VMWare Tools, if it's installed - the ID may vary
  $hasVmwareTools = $False
  $productsDirPath = ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Classes\Installer\Products\")
  $productPaths = REG QUERY $productsDirPath
  # Loop through the products looking for the ID of VMware Tools, if its installed
  ForEach($productPath in $productPaths) {
    if ("$productPath" -eq ""){ continue }
      $name = REG QUERY $productPath /v ProductName 2> $null
      if (!$?){ continue }
      ForEach($line in $name){
        if ($line -like "*VMware Tools"){
          $hasVmwareTools = $True
          $vmwareId = $productPath.Split("\") | Select-Object -Last 1
        }
      }
    }
  # Now that we know it's installed and have the ID, clean up those entries
  if ($hasVmwareTools){
    $keys = @(
      ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Classes\Installer\Features\" + $vmwareId),
      ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Classes\Installer\Products\" + $vmwareId),
      ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Microsoft\Windows\CurrentVersion\Installer\UserData\S-1-5-18\Products\" + $vmwareId),
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
    $uiPaths = REG QUERY ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Microsoft\Windows\CurrentVersion\Uninstall")
    $removedUiKey = $False
    ForEach ($uiPath in $uiPaths){
      if ("$uiPath" -eq "") { continue }
      $displayName = REG QUERY $uiPath /v DisplayName 2> $null
      if (!$?){ continue }
      ForEach($line in $displayName){
        if ($line -like "*VMware Tools"){
          Write-Host REG DELETE "`"$uiPath`"" /f
          REG DELETE "`"$uiPath`"" /f
          $removedUiKey = $True
          break
        }
      }
      if ($removedUiKey){ break }
    }
  }
  # Remove the service registry keys
  $controlSetPaths = REG QUERY $HKEY_LOCAL_MACHINE_SYSTEM | where {$_ -like "*ControlSet*"}
  $services = @("VMTools", "vm3dservice", "vmvss", "VGAuthService")
  ForEach ($controlSetPath in $controlSetPaths){
    ForEach ($service in $services){
      $serviceKey = ($controlSetPath + "\Services\" + $service)
      REG QUERY $serviceKey > $null 2> $null
      if ($?){
        Write-Host REG DELETE $serviceKey /f
        REG DELETE $serviceKey /f
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
    ($letter + ":\Program Files\VMware"),
    ($letter + ":\Program Files (x86)\VMware")
  )
  ForEach($folder in $folders){
    if ($(Test-Path $folder)){
      Write-Host Remove-Item -Recurse -Force $folder
      Remove-Item -Recurse -Force $folder
    }
  }
}


function Get-BootStyle {
  param(
    [Parameter(Position = 0, ValueFromPipeline = $true, ValueFromRemainingArguments = $true)]
    [PSObject]$BootPartition
  )
  # Check if UEFI or BIOS is needed to boot the mounted VM's BootPartition
  $disk = Get-Disk -Number $BootPartition.DiskNumber
  $style = $disk.PartitionStyle
  Write-Host "Disk Partition Style: $style"
  $type = "UNKNOWN"
  if ($style -eq "MBR"){
    $type = "BIOS"
  } elseif ($style -eq "GPT"){
    $type = "UEFI"
  }
  Write-Host "Boot Type: $type"
}



# Export the functions
Export-ModuleMember -Function Get-TargetBootPartition
Export-ModuleMember -Function Add-VirtioDrivers
Export-ModuleMember -Function Get-PartitionDrivers
Export-ModuleMember -Function Remove-VMwareTools
Export-ModuleMember -Function Get-BootStyle
Export-ModuleMember -Function Repair-OfflineDisks
