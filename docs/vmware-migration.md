# Exporting VMs to OpenStack from VMware

The `voithos vmware` commands leverage VMware's powerful Python libraries to help identify and
export VMs to other platforms. The process of exporting a VM from VMware to OpenStack is as
follows:

1. Create worker VMs: An Ubuntu worker is always needed. For Windows, a Windows Server is too.
    1. [Creating a Linux migration worker](/migrations/linux-worker.html)
    1. [Creating a Windows migration worker](/migrations/windows-worker.html)
1. Using the [Voithos VMware utilities](/vmware-utils.html):
    1. Find the VMware VM's UUID with `voithos vmware show-vm`
    1. Download the VMware VM to the Linux worker with `voithos vmware download-vm`
1. Using the [Voithos qemu-img utility](/qemu-img.html), determine the size of each VMware VM
   volume - `voithos util qemu-img show`
1. Create appropriately sized Cinder volumes: 
`openstack volume create --type <volume type> --size <raw size> <volume name>` 
1. Attach the volumes to the Linux migration worker:
   `openstack server add volume <server> <volume>`
1. Using the [Voithos qemu-img utility](/qemu-img.html), write the VMDK files to the Cinder
   volumes: with `voithos util qemu-img convert`
1. Create the Neutron ports - note their Mac addresses
   1. With a specific IP address:
      `openstack port create --network <network> --fixed-ip subnet=<subnet>,ip-address=<ip-address> <interface name>`
   1. With any IP address: `openstack port create --network <network> <interface name>`
1. Perform any OS-dependent conversion steps
    1. [Red-Hat/CentOS Linux](/migrations/rhel-conversion.html)
    1. [Windows Server/Client](/migrations/windows-conversion.html)
1. Set the Cinder boot volume as `bootable`: `openstack volume set --bootable <volume>`
1. (If needed) set Cinder the boot volume to use UEFI boot:
   `openstack volume set --image-property hw_firmware_type=uefi <volume>`
1. [Create a server using the existing volumes and NICs](/migrations/cli-openstack-server-creation.html):
   `openstack server create`
