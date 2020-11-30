# Exporting VMs to OpenStack from VMware

The `voithos vmware` commands leverage VMware's powerful Python libraries to help identify and
export VMs to other platforms.

## Create a temporary migration worker VM

When importing a VM into OpenStack, first create a migration worker VM on the cloud, inside the
project where the VM is to be imported. This VM should use a Linux OS and it must have both Voithos
and Docker installed. Currently an outbound internet connection is also required to pull images
from Docker Hub. It can also be helpful to install the OpenStack client on this worker, though that
isn't strictly necessary.

If you're using an Ubuntu 18.04 VM, these steps will effectively configure it as a migration
worker:

```bash
# Install Docker and Python3
apt-get update
apt-get install docker.io python3 python3-pip virtualenv

# In your home directory, create a virtualenv and install Voithos
cd
virtualenv --python=python3 env/
source env/bin/activate
pip install git+https://github.com/breqwatr/voithos.git
# Optional, but the client must be installed *somewhere*
pip install python-openstackclient
```


### Optional - Set VMware environment variables

The `voithos vmware` commands can be used in two ways. Either every call can set the `--username`,
`--password` and `--ip-addr` options, or environment variables can be defined. If you lead the
`export` commands with a space, they won't be saved to your bash history.

```bash
 export VMWARE_USERNAME=
 export VMWARE_PASSWORD=
 export VMWARE_IP_ADDR=
```


## Identify the VM to move

To download the VM you will need to find its UUID.

The `show-vms` command supports three formats with the `--format` or `-f` option:

- (default) `pprint`, or "pretty print", format is the easiest to read. Its like formatted JSON.
- `csv` is the easiest to use when looking for a VM's UUID. Its output can be redirected to a file
  for use in a spreadsheet.
- `json` is intended to enable scripting, typically with the `jq` command.

To find a VM, pass all or part of its name to the `-n` or `--name` option. To list multiple VMs you
can also pass that option more than once. If a name equals `*` then all VMs will be returned.


**Examples**:

```bash
# To find a VM named rhel-test1:
voithos vmware show-vm -n rhel-test1

# to show it in json or csv format:
voithos vmware show-vm -n rhel-test1 -f csv
voithos vmware show-vm -n rhel-test1 -f json

# List all VMs with the word "test" in their name
voithos vmware show-vm -n test

# list ALL vms in the given VMware environment, and send them to a CSV
voithosvmware show-vm -n "*" -f csv
```


## Export / Download the VM

Once you have the VMs UUID, you can use it for the `<UUID>` positional argument of the
`download-vm` command:

```bash
voithos vmware download-vm <UUID>
```


## Create and Attach Cinder volumes

### Determine Volume Size

For each downloaded VMDK file, determine its "thick" size.

```bash
# The full raw size is shown as "virtual size"
voithos util qemu-img show <disk file>
```

### Create and Attach blank volumes to worker VM

**NOTE**: It's often a good idea to restart the worker VM before moving to the next VM. If previous
volumes used LVM then the VM can end up in a messy state that rebooting resolves.

Create empty Cinder volumes to hold the data and attach them to the worker. Be sure to scope to
the correct project.

For the boot (first) volume set `--bootable`.

```bash
# Repeat this procedure for each volume
openstack volume create --type <volume type> <--bootable> --size <size> <vol-name>
openstack server add volume <server> <volume>
```

For example:

```bash
vmware_vm_name="test-centos-1"
voithos util qemu-img show test-centos-1-1.vmdk  | grep "virtual size"
openstack volume create --type ceph --bootable --size 20 "$vmware_vm_name-sda"
woker_vm_id="54dbc520-b665-4186-b4bb-8da829c1c1ed"
openstack server add volume $woker_vm_id "$vmware_vm_name-sda"
```

On the worker VM you should be able to see that the disk was attached from the output of `dmesg`,
and it should display in `fdisk -l` with the appropriate size.


## Copy VMDK data into Cinder volumes

Use the `qemu-img convert` command to copy the data to the volume. If it isn't installed locally,
we've built it into Voithos.

```bash
voithos util qemu-img convert -f vmdk -O raw <vmdk file> <device path>
```

For example:

```bash
voithos util qemu-img convert -f vmdk -O raw test-centos-1-1.vmdk /dev/vdb
```

If the disk had any partitions on it, you'll see them now with `fdisk -l`.

To see any new LVM volumes, run:

```bash
partprobe
pvscan
lvdisplay
```


---

# VMWare-to-KVM Conversion

The Volume is now imported into OpenStack! Unfortunately most of the time the work isn't done
there. Generally the VM won't boot until you at least add some virtio drivers to it, and you might
need to modify it further to ensure the networking works as you'd expect.

Check the following guides to finish migrating your workload:

- [Migrations: RedHat Linux](/vmware-migration-rhel.html)


---

# Booting the OpenStack Server

If uncertain, check
[the official documentation](https://docs.openstack.org/python-openstackclient/train/cli/command-objects/server.html).

## Remove volumes from migration workers

If the volumes are still attached to a Windows/Linux migration worker, remove them.

```bash
openstack server remove volume kyle-dev 17860215-23a2-4156-9087-8c87a01360bc
```


## Determine which flavor to use

```bash
# Determine the RAM & CPU requirements
voithos vmware show-vm -n <vm name>
openstack flavor list
```

Given the source VM's configuration, select an appropriate flavor.

## Configure server networking

List the OpenStack networks in this project scope:

```bash
openstack network list
```

### Single Dynamic IP interface

When creating a server that will have a brand new IP address, it's easiest just to use the
`--network <network>` option of `openstack server create`:

```bash
# example
openstack server create --network VLAN-100-net
```

### Static IP assignment / Multi-interface

When building a VM to use a manually chosen IP, such as when using a static IP address with
port-security turned on, the `--nic` option should be used instead. This argument can be used
multiple times.

**Note:** The admin role is required in the scoped project to assign a specific IP address. Without
admin rights an error is raised on the VM saying `Exceeded max scheduling attempts` and
`rule:create_port:fixed_ips and (rule:create_port:fixed_ips:ip_address))) is disallowed by policy`.


```bash
# [--nic <net-id=net-uuid,v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr,port-id=port-uuid,auto,none>]
# example
openstack server create net-id=02a4eaaf-bb3e-4491-b80b-9c4021771198,v4-fixed-ip=192.168.0.11
```


## Define volumes at boot-time

The boot volume should use the `--volume <volume>` option.
Additional volumes should use `--block-devicemapping` options with incrementing `vdb`, `vdc`, `vdd`
(and so on) keys.

```bash
# example
openstack server create \
  --volume server-vol-1 \
  --block-device-mapping vdb=server-vol-2 \
  --block-device-mapping vdc=server-vol-3
```


## Example

```bash
flavor="dd88ed34-6bc2-4b15-b00d-0c83f71d1674"
boot_vol="test-centos-1-sda"
data_vol="test-centos-1-sdb"
network="dae7c823-e15a-4409-b9ca-45e7c2849349"
name="test-centos-1"
openstack server create \
  --flavor $flavor \
  --volume $boot_vol \
  --block-device-mapping vdb=$data_vol \
  --nic net-id=$network,v4-fixed-ip=10.106.2.222 \
  $name
```
