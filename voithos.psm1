 # ps1

# Voithos Powershell Module
# Maintained by Breqwatr - info@breqwatr.com

# Save to:     C:\Program Files\WindowsPowerShell\Modules\Modules\Voithos\voithos.psm1
# Import CMD:  Import-Module Voithos
# Description: Provides Windows automation functions, particularly for migrating VMWARE->KVM


function Add-HklmRegistryHive {
  param(
    [Parameter(Mandatory=$True)]  [PSObject] $BootPartition,
    [Parameter(Mandatory=$True)]  [string]   $Hive
  )
  ### Load the given HKLM hive from the specified partition as TEMP$HIVE ###
  # Common values for Hive: SOFTWARE, SYSTEM, SECURITY
  $hklmPath = ($BootPartition.DriveLetter + ":\Windows\System32\Config\$Hive")
  Write-Host REG LOAD "HKLM\TEMP$Hive" $hklmPath
  REG LOAD "HKLM\TEMP$Hive" $hklmPath | Out-Null
  return "HKLM:\TEMP$Hive"
}


function Remove-HklmRegistryHive {
  param(
    [Parameter(Mandatory=$True)]  [string] $Hive
  )
  ### Unload HKLM\TEMP$Hive ###
  Write-Host REG UNLOAD "HKLM\TEMP$Hive"
  REG UNLOAD "HKLM\TEMP$Hive" | Out-Null
}


function Get-HklmRegistryValue {
  param(
    [Parameter(Mandatory=$True)] [string]   $Hive,
    [Parameter(Mandatory=$True)]  [string]   $KeyPath,
    [Parameter(Mandatory=$False)] [string]   $KeyName,
    [Parameter(Mandatory=$True)]  [PSObject] $BootPartition,
    [Switch] $RelativePath=$True
  )
  ### Return the value of a given registry key in the HKLM/$Hive hive ###
  $hivePath = Add-HklmRegistryHive -BootPartition $BootPartition -Hive $Hive
  $queryPath = ($KeyPath -Replace "HKEY_LOCAL_MACHINE\\","HKLM:\")
  if ($RelativePath) {
    $queryPath = "$hivePath\$KeyPath"
  }
  try {
    $result = Get-ItemProperty $queryPath
  } catch {
    return $Null
  } finally {
    Remove-HklmRegistryHive -Hive $Hive
  }
  if ($KeyName -eq $Null -or $KeyName -eq "") { 
    return $result 
  } else {
    return ($result | Select-Object -ExpandProperty $KeyName) 
  }
}


function Get-HklmRegistryChildKey {
  param(
    [Parameter(Mandatory=$True)] [string] $Hive,
    [Parameter(Mandatory=$False)] [string] $KeyPath="",
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
  )
  ### Return the child registry keys of the given Hive/KeyPath ###
  $hivePath = Add-HklmRegistryHive -BootPartition $BootPartition -Hive $Hive
  try {
    $result = Get-ChildItem -Path "$hivePath\$KeyPath"
    $result.Handle.Close()  # Close the registry connection else Access Denied on Unload
    $names = $result | Select-Object -ExpandProperty Name
  } finally {
    Remove-HklmRegistryHive -Hive $Hive
  }
  return $names
}

function Set-HklmRegistryValue {
    [Parameter(Mandatory=$True)] [string] $Hive,
    [Parameter(Mandatory=$True)] [string] $KeyPath,
    [Parameter(Mandatory=$True)] [string] $KeyName
    # TODO: This
}


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


function Save-CloudBaseInit {
  # Download the cloudbase init installer
  $path = "C:\CloudbaseInitSetup.msi"
  $exists = Test-Path $path
  if (!$exists){
    Write-Host "Cloudbase-init archive not found - downloading to $path"
    $url = "https://cloudbase.it/downloads/CloudbaseInitSetup_Stable_x64.msi"
    (New-Object System.Net.WebClient).DownloadFile($url, $path)
  }
  return $path
}


function Save-VirtioISO {
  # Download the Virtio ISO file if its missing - Return the path to the file
  $path = "C:\virtio.iso"
  $exists = Test-Path $path
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


function Get-MountedWindowsVersion {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
  )
  return Get-HklmRegistryValue `
    -Hive SOFTWARE `
    -KeyPath "Microsoft\Windows NT\CurrentVersion" `
    -KeyName "ProductName" `
    -BootPartition $BootPartition
}


function Add-VirtioDrivers {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition,
    [Parameter(Mandatory=$False)] [PSObject] $Distro
  )
  $distroOptions = @("w7", "w8", "w8.1", "2k12", "2k12r2", "2k16", "2k19")
  Write-Host "Valid -Distro values: $distroOptions"
  if (! $distroOptions.Contains($Distro)){
    return "ERROR: Invalid -Distro value"
  }
  $windowsVersion = Get-MountedWindowsVersion -BootPartition $BootPartition
  Write-Host "Provided Distro value: $Distro"
  Write-Host "Detected Windows Version: $windowsVersion"
  $confirm = Read-Host -Prompt "Continue? [y/N]"
  if ($confirm -ne "y" -and $confirm -ne "Y") {
    return "Quitting"
  }
  # Install all of the VirtIO drivers for the given OS using DISM on the selected BootPartition
  $virtio_drive = $(Get-VirtioVolume).DriveLetter + ":\"
  $drivers = Get-ChildItem  -Recurse $virtio_drive | Where-Object {
    $_.PSIsContainer -eq $true -and $_.Name -eq "amd64" -and $_.Parent.Name -eq $Distro
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
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
  )
  # Run DISM /Get-Drivers on the given partition
  $bootVol = $BootPartition.DriveLetter +":/"
  Write-Host "DISM /Image:$bootVol /Get-Drivers"
  DISM /Image:$bootVol /Get-Drivers
}


function Remove-VMwareTools {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
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
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
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


function Set-InterfaceAddress {
  param(
    [Parameter(Mandatory=$True)]  [string] $MacAddress,
    [Parameter(Mandatory=$True)]  [string] $IPAddress,
    [Parameter(Mandatory=$True)]  [string] $SubnetPrefix,
    [Parameter(Mandatory=$false)] [string] $GatewayIPAddress,
    [Parameter(Mandatory=$false)] [string] $DNSAddressCSV
  )
  # Convert mac address format
  # Openstack format: fa:16:3e:5e:de:ce --> Windows format: FA-16-3E-5E-DE-CE
  $MacAddress = ($MacAddress -Replace ":","-").ToUpper()
  $nic = Get-NetAdapter | Where-Object MacAddress -eq $MacAddress
  if (! $nic){
    Write-Host "ERROR: Failed to find NIC with MAC address $MacAddress"
    return
  }
  Remove-NetIPAddress -InterfaceIndex $nic.ifIndex -Confirm:$False
  $newIPAddress = New-NetIPAddress -InterfaceIndex $nic.ifIndex -IPAddress $IPAddress -PrefixLength $SubnetPrefix
  if ($GatewayIPAddress){
    $gwPrefix = "0.0.0.0/0"
    Get-NetRoute | Where-Object DestinationPrefix -eq $gwPrefix | Remove-NetRoute -Confirm:$False
    New-NetRoute -InterfaceIndex $nic.ifIndex -DestinationPrefix $gwPrefix -NextHop $GatewayIPAddress | Out-Null
  }
  if ($DNSAddressCSV){
    $dnsAddresses = $DNSAddressCSV.Split(",")
    Set-DnsClientServerAddress -InterfaceIndex $nic.ifIndex -ServerAddresses $dnsAddresses | Out-Null
  }
  return $newIPAddress[0]
}


function Copy-VoithosModuleToBootPartition {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
  )
  # Write the Voithos module to the migration target's boot partition
  $src = "$Env:ProgramFiles\WindowsPowerShell\Modules\Voithos"
  $dest1 = ($BootPartition.DriveLetter + ":\Program Files (x86)\WindowsPowerShell\Modules\")
  Copy-Item -Recurse -Path $src -Destination $dest1 -Force | Out-Null
  Get-Item $dest1
  $dest2 = ($BootPartition.DriveLetter + ":\Program Files\WindowsPowerShell\Modules\")
  Copy-Item -Recurse -Path $src -Destination $dest2 -Force | Out-Null
  Get-Item $dest2
}


function New-StartupScript {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
  )
  $scriptDir = ($BootPartition.DriveLetter + ":\Windows\System32\GroupPolicy\Machine\Scripts\Startup\")
  Write-Host "Create: $scriptDir"
  New-Item -ItemType Directory -Force -Path $scriptDir
  $path = ($scriptDir + "\startup.ps1")
  Write-Host "Edit: $path"
  notepad $path
}


function Set-RunOnceScript {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition,
    [Parameter(Mandatory=$True)] [string] $ScriptPath
  )
  $hklmPath = ($BootPartition.DriveLetter + ":\Windows\System32\Config\SOFTWARE")
  $HKEY_LOCAL_MACHINE_SOFTWARE = "HKLM\TEMPSOFTWARE"
  Write-Host "REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath"
  REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath
  $runOnceKey = ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Microsoft\Windows\CurrentVersion\RunOnce")
  $runOnceVal = "PowerShell.exe -executionpolicy bypass -file C:\Breqwatr\startup.ps1"
  Write-Host "REG ADD $runOnceKey /ve /t REG_SZ /d $runOnceVal /f"
  REG ADD $runOnceKey /ve /t REG_SZ /d $runOnceVal /f
  Write-Host "REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE"
  REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE
}


function Get-RunOnceScript {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
  )
  $hklmPath = ($BootPartition.DriveLetter + ":\Windows\System32\Config\SOFTWARE")
  $HKEY_LOCAL_MACHINE_SOFTWARE = "HKLM\TEMPSOFTWARE"
  Write-Host "REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath"
  REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath
  $runOnceKey = ($HKEY_LOCAL_MACHINE_SOFTWARE + "\Microsoft\Windows\CurrentVersion\RunOnce")
  Write-Host "REG QUERY $runOnceKey"
  REG QUERY $runOnceKey
  Write-Host "REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE"
  REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE
}

function Set-AllDisksOnline {
  $offDisks = Get-Disk | Where-Object OperationalStatus -eq "Offline"
  $offDisks | Set-Disk -isOffline $False
  $offDisks | Set-Disk -isReadOnly $False
}


function Set-GPOStartupScript {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $DriveLetter,
    [Parameter(Mandatory=$True)] [PSObject] $SoftwareHivePath,
    [Parameter(Mandatory=$True)] [string] $ScriptPath
  )
  #
  $letter = $DriveLetter
  $HKEY_LOCAL_MACHINE_SOFTWARE = $SoftwareHivePath
  $scripts = "$HKEY_LOCAL_MACHINE_SOFTWARE\Microsoft\Windows\CurrentVersion\Group Policy\State\Machine\Scripts"
  Write-Host "Creating REG keys at $scripts"
  REG ADD "$scripts" /f | Out-Null
  REG ADD "$scripts\Startup" /f  | Out-Null
  REG ADD "$scripts\Shutdown" /f  | Out-Null
  REG ADD "$scripts\Startup\0" /f  | Out-Null
  REG ADD "$scripts\Startup\0" /v DisplayName /t REG_SZ /d "Local Group Policy" /f  | Out-Null
  REG ADD "$scripts\Startup\0" /v FileSysPath /t REG_SZ /d "C:\Windows\System32\GroupPolicy\Machine" /f  | Out-Null
  REG ADD "$scripts\Startup\0" /v GPO-ID /t REG_SZ /d "LocalGPO" /f  | Out-Null
  REG ADD "$scripts\Startup\0" /v GPOName /t REG_SZ /d "Local Group Policy" /f  | Out-Null
  REG ADD "$scripts\Startup\0" /v PSScriptOrder /t REG_DWORD /d 1 /f  | Out-Null
  REG ADD "$scripts\Startup\0" /v SOM-ID /t REG_SZ /d "Local" /f  | Out-Null
  REG ADD "$scripts\Startup\0\0" /f  | Out-Null
  REG ADD "$scripts\Startup\0\0" /v Parameters /t REG_SZ /f  | Out-Null
  # 
  $regScriptPath = $ScriptPath
  if ($scriptPath -like "*GroupPolicy\Machine\Scripts\Startup*") {
    # When the script is in this directory you reference it with a relative path
    $regScriptPath = $scriptPath.Split("\")[-1]
  }
  Write-Host REG ADD "$scripts\Startup\0\0" /v Script /t REG_SZ /d "$regScriptPath" /f
  REG ADD "$scripts\Startup\0\0" /v Script /t REG_SZ /d "$regScriptPath" /f | Out-Null
  #
  # Set the psscriptfile.ini contents to point to the script
  $psscriptFile = ($letter + ":\Windows\System32\GroupPolicy\Machine\Scripts\psscripts.ini")
  $psscriptContent = "
[Startup]
0CmdLine=$ScriptPath
0Parameters=
 
"
  Attrib -h $psscriptFile
  Write-Host "Creating: $psscriptFile"
  New-Item -ItemType Directory -Force -Path ($letter + ":\Windows\System32\GroupPolicy\Machine\Scripts") | Out-Null
  $psscriptContent | Out-File -Force -Confirm:$False -Encoding unicode -FilePath $psscriptFile
  Get-Content $psscriptFile
  Attrib +h $psscriptFile
  #
  # Set the gpt.ini to have the guid of the startup script and increase the version
  $gptFile = ($letter + ":\Windows\System32\GroupPolicy\gpt.ini")
  $version = ((get-random) % 100)
  $gptContent="[General]
gPCMachineExtensionNames=[{42B5FAAE-6536-11D2-AE5A-0000F87571E3}{40B6664F-4972-11D1-A7CA-0000F87571E3}]
Version=$version"
  Attrib -h $gptFile
  Write-Host "Creating: $gptFile"
  $gptContent | Out-File -Force -Confirm:$False -Encoding ascii -FilePath $gptFile
  Get-Content $gptFile
}


function Set-MountedGPOStartupScript {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
  )
  $letter = $BootPartition.DriveLetter
  $hklmPath = ($letter + ":\Windows\System32\Config\SOFTWARE")
  $HKEY_LOCAL_MACHINE_SOFTWARE = "HKLM\TEMPSOFTWARE"
  Write-Host "REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath"
  REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath
  if (! $?) {
    Write-Error "Failed to load registry hive"
    return
  }
  #
  $scriptPath = "C:\Windows\System32\GroupPolicy\Machine\Scripts\Startup\startup.ps1"
  Set-GPOStartupScript -DriveLetter $letter -SoftwareHivePath $HKEY_LOCAL_MACHINE_SOFTWARE -ScriptPath $scriptPath
  #
  Write-Host "REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE"
  REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE  
}


Function Backup-LocalGPOSettings {
  param(
    [Parameter(Mandatory=$False)] [string] $DriveLetter="C",
    [Parameter(Mandatory=$False)] [string] $Hive="HKLM\SOFTWARE"
  )
  $letter = $DriveLetter
  $HKEY_LOCAL_MACHINE_SOFTWARE = $Hive
  # Save the registry scripts keys
  $backupDir = ($letter + ":\Breqwatr")
  New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
  Write-Host "Created: $backupDir"
  #
  $scripts = "$HKEY_LOCAL_MACHINE_SOFTWARE\Microsoft\Windows\CurrentVersion\Group Policy\State\Machine\Scripts"
  REG QUERY $scripts 2>&1 | Out-Null
  $hadScripts = $?
  if ($hadScripts){
    $backupFile = "$backupDir\GpoScriptsBackup.reg"
    REG EXPORT $scripts $backupFile /y | Out-Null
    Write-Host "Created: $backupFile"
  }
  else {
    Write-Host "$scripts not found - Not backing it up"
  }
  # Save the GroupPolicy folder
  $gpoFolderPath = ($letter + ":\Windows\System32\GroupPolicy")
  if (Test-Path $gpoFolderPath) {
    $gpoFolderBackupPath = ($letter + ":\Breqwatr\GroupPolicyBackup")
    Remove-Item -Recurse -Force -Confirm:$False -Path $gpoFolderBackupPath 2>$Null
    Copy-Item -Recurse -Path $gpoFolderPath $gpoFolderBackupPath -Force
    Write-Host "Created: $gpoFolderBackupPath"
  } else {
    Write-Host "$gpoFolderPath not found - Not backing it up"
  }
}


Function Backup-MountedLocalGPOSettings {
  param(
    [Parameter(Mandatory=$True)] [PSObject] $BootPartition
  )
  #
  # Load the hive
  $letter = $BootPartition.DriveLetter
  $hklmPath = ($letter + ":\Windows\System32\Config\SOFTWARE")
  $HKEY_LOCAL_MACHINE_SOFTWARE = "HKLM\TEMPSOFTWARE"
  Write-Host "REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath"
  REG LOAD $HKEY_LOCAL_MACHINE_SOFTWARE  $hklmPath
  if (! $?) {
    Write-Error "Failed to load registry hive"
    return
  }
  #
  Backup-LocalGPOSettings -DriveLetter $letter -Hive $HKEY_LOCAL_MACHINE_SOFTWARE
  # Unload the hive
  Write-Host "REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE"
  REG UNLOAD $HKEY_LOCAL_MACHINE_SOFTWARE
  Write-Host "Backup completed"
}


function Remove-GPOStartupScript {
  # Remove any GPO startup script and all of its associated files
  Write-Host REG DELETE "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Group Policy\State\Machine\Scripts\0" /f
  REG DELETE "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Group Policy\State\Machine\Scripts\0" /f 2>$Null
  #
  $startupScriptPath = "C:\Windows\System32\GroupPolicy\Machine\Scripts\Startup\startup.ps1"
  Write-Host "Removing startup script: $startupScriptPath"
  Remove-Item $startupScriptPath -Confirm:$False -Force 2>$Null
  # 
  # Set the gpt.ini to have the guid of the startup script and increase the version
  $gptFile = "C:\Windows\System32\GroupPolicy\gpt.ini"
  Write-Host "Blanking $gptFile"
  $gptContent="[General]
gPCMachineExtensionNames=
Version=1"
  Attrib -h $gptFile
  $gptContent | Out-File -Force -Confirm:$False -Encoding ascii -FilePath $gptFile
  #
  # Remove psscripts.ini
  $psscriptFile = "C:\Windows\System32\GroupPolicy\Machine\Scripts\psscripts.ini"
  Write-Host "Removing: $psscriptFile"
  Remove-Item $psscriptFile -Confirm:$False -Force 2>$Null
 
}


function Reset-GPOStartupScript {
  # Restore the backed up GPO settings
  if (! (Test-Path "C:\Breqwatr" 2>$null)) {
    Write-Host "C:\Breqwatr not found - Quitting (nothing to restore from)"
    return
  }
  $regBackupFile = "C:\Breqwatr\GpoScriptsBackup.reg"
  if (Test-Path $regBackupFile) {
    Write-Host REG IMPORT $regBackupFile
    REG IMPORT $regBackupFile
  } else {
    Write-Host "Registry backup file not found: $regBackupFile"
  }
  $gpoFolderBackupPath = "C:\Breqwatr\GroupPolicyBackup"
  if (Test-Path $gpoFolderBackupPath) {
    $gpoFolderPath = "C:\Windows\System32\GroupPolicy"
    Write-Host "Copying $gpoFolderBackupPath to $gpoFolderPath"
    Remove-Item -Path $gpoFolderPath -Recurse -Confirm:$False -Force
    Copy-Item -Recurse -Path $gpoFolderBackupPath -Destination $gpoFolderPath -Force
  } else {
    Write-Host "GPO backup folder not found: $gpoFolderBackupPath"
  }
}


###################################################################################################
###################################################################################################

# Publc Function Exports
Export-ModuleMember -Function Get-TargetBootPartition
Export-ModuleMember -Function Get-MountedWindowsVersion
Export-ModuleMember -Function Add-VirtioDrivers
Export-ModuleMember -Function Get-PartitionDrivers
Export-ModuleMember -Function Remove-VMwareTools
Export-ModuleMember -Function Get-BootStyle
Export-ModuleMember -Function Repair-OfflineDisks
Export-ModuleMember -Function Copy-VoithosModuleToBootPartition
Export-ModuleMember -Function Set-InterfaceAddress
Export-ModuleMember -Function New-StartupScript
Export-ModuleMember -Function Get-RunOnceScript
Export-ModuleMember -Function Set-RunOnceScript
Export-ModuleMember -Function Set-AllDisksOnline
Export-ModuleMember -Function Backup-LocalGPOSettings
Export-ModuleMember -Function Backup-MountedLocalGPOSettings
Export-ModuleMember -Function Set-GPOStartupScript
Export-ModuleMember -Function Set-MountedGPOStartupScript
Export-ModuleMember -Function Remove-GPOStartupScript
Export-ModuleMember -Function Reset-GPOStartupScript 
