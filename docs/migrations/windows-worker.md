[Back to the migration guide](/vmware-migration.html)


# Creating a Windows wigration worker

The Windows migration worker mounts the volumes of Windows import targets and modifies them.

- It uses DISM to inject drivers
- It can load and edit Registry hives
- It can modify and remove files on the migration target's disks

The operating system of the Windows worker must be as new or newer than the migration target. We
currently test using Windows Server 2019.

**Requirements**:

- The VM must exist inside the same OpenStack project where the migration target VM will be created
- Outbound internet connection


# Deploy the Voithos powershell module

Open a Powershell terminal as administrator and execute the following:

```ps1
# Create the module dir
$modulesDir = "$Env:ProgramFiles\WindowsPowerShell\Modules\Voithos"
New-Item -ItemType Directory -Path $modulesDir

# Download the Powershell module
$url = "https://raw.githubusercontent.com/breqwatr/voithos/master/powershell/voithos.psm1"
$output = "$modulesDir\voithos.psm1"
Invoke-WebRequest $url -OutFile $output

# Download the registry file
$url = "https://raw.githubusercontent.com/breqwatr/voithos/master/powershell/gpoStartupScript.reg"
$output = "$modulesDir\gpoStartupScript.reg"
Invoke-WebRequest $url -OutFile $output
```

This will enable the command `Import-Module Voithos` and download a GPO export that will only run
a startup script called startup.ps1
