# Creating a Windows wigration worker

The Windows migration worker mounts the volumes of Windows import targets and modifies them.

- It uses DISM to inject drivers
- It can load and edit Registry hives
- It can modify and remove files on the migration target's disks

The operating system of the Windows worker must be as new or newer than the migration target. We
currently test using Windows Server 2019.

Requirements:
- Must exist inside the same OpenStack project where the migration target VM will be created
- Outbound internet connection

No special configuration is required, though it can be helpful to download our conversion scripts.
