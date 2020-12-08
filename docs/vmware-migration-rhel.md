# Migrating RedHat Linux from VMware to OpenStack


## Requirements

Before this guide can be followed:

 - The virtual volumes of the VM must have already been imported into Cinder.
   If that hasn't been done yet, follow [this guide](/vmware-migration.html) first.
 - The migration worker VM must be online and have the newly imported cinder volumes attached.
 - If the volumes use LVM, ensure the volumes can be seen in `lvdisplay`.
 - The OpenStack Neutron ports that this VM will use have been created.
   Collect their MAC addresses to be used below.


---


## (optional) Repair the file-systems

If desired, `fsck` the partition while you're in the neighbourhood. It can be a good idea to do
this against each partition while they're mounted here. You'll never have a better opportunity.

```bash
# show the filesystem
blkid /dev/mapper/cl-root
# in this case it's xfs
xfs_repair /dev/mapper/cl-root
```


---


## Create & enter the chroot

The `chroot` command allows us to enter a mounted root file-system as if we were SSH'ing into a
running VM. Think of how Docker works, it's the same underlying concept.

Since the migration target VM's volumes are mounted to the migration worker, we can `chroot` into
it and make changes.


### Mount the boot partition

Figure out which partition is the boot partition for the VM to be migrated. Often it will be a
small partition at the start of the boot disk. `fdisk` will show an `*` in the boot column for that
partition. For example:

```
fdisk -l
# ...
Device     Boot   Start      End  Sectors Size Id Type
/dev/vdb1  *       2048  2099199  2097152   1G 83 Linux
/dev/vdb2       2099200 41943039 39843840  19G 8e Linux LVM
```

Once you know which one is boot, mount it:

```bash
# Example:
mkdir -p /mnt/boot
mount /dev/vdb1 /mnt/boot
```


### Mount the root partition

The root partition can be harder to find. In the above example, the second boot disk partition uses
LVM, so it's an LVM partition. Often there's an LV with `root` in its name. If not, you'll have to
do some detective work. Usually the volume that has `etc/fstab` in it is the root volume.

List the LV's:

```bash
lvdisplay -C -o "lv_name,lv_path,lv_dm_path"
```

For the sake of these examples, the root LV's device mapper path will be `/dev/mapper/cl-root`. Be
sure to use the correct one for your VM.

```
mkdir -p /mnt/root
mount /dev/mapper/cl-root /mnt/root
```


### Bind-mount to the root volume

Bind-mount the boot volume.

```bash
mount --bind /mnt/boot /mnt/root/boot
```


### (optional) Mount other required partitions

**Note:** This usually isn't needed.


Take a look at the `/etc/fstab` file of this VM. If it mounts other LV's or partitions, mount them
into `/mnt` on your worker VM too. They'll be bind-mounted into the root volume in the next step.
Don't worry about any swap mounts.

```bash
cat /mnt/root/etc/fstab
# mount --bind <source> /mnt/root/<dest>
```


### Enter the chroot

```bash
chroot /mnt/root /bin/bash
```

---


## Add Virtio drivers to initrd files

In many releases of RedHat, the VM will boot to `dracut >` when imported into OpenStack unless you
manually inject the Virtio drivers to the initrd files.


Get the Kernel version. The initrd files will have the same version strung.
Use it to add the drivers by calling `dracut` command.

```bash
# Get the version
version=$(rpm -q kernel --queryformat "%{VERSION}-%{RELEASE}.%{ARCH}\n" | sort -V | head -n 1)

# Check if the drivers are already installed
filename="/boot/initramfs-$version.img"
lsinitrd $filename | grep virtio

# If nothing is returned ("$?" == "1") then add the drivers with dracut
dracut -f $filename $version --add-drivers "virtio_blk virtio_net virtio_scsi virtio_balloon"

# ignore issues regarding /bin and /proc/* being missing
# confirm the drivers are there now
lsinitrd $filename | grep virtio
```

The kernel driver files should appear in the final `lsinitrd` command output.


---


## Remove Installed software

From inside the `chroot` entered while installing the virtio drivers:


### Remove VMWare Tools

VMware tools shouldn't hurt anything on KVM/OpenStack, but we don't need it either.

```bash
rpm -qa | grep "vm-tools" | while read pkg; do echo "removing $pkg"; rpm -e $pkg; done
```


### Remove Cloud-Init

Sometimes cloud-init will already be installed in a VM. While generally nice to have, it causes all
sorts of problems during migrations. Usually it's best to simply remove it:

```bash
rpm -qa | grep cloud-init | while read pkg; do echo "removing $pkg"; rpm -e $pkg; done
```


---


## Configure Networking


### Configure consistent network device naming

The network adapters will probably change their names when they move to the new cloud.
Since the interface names can be unpredictable, use the
"[consistent network device naming](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/networking_guide/ch-consistent_network_device_naming)"
udev rules with MAC addresses to enforce the device names.

If you haven't made the ports in OpenStack yet for this VM, now's the time.

Here's an example of a server with two interfaces. One line per interface.

`vi /etc/udev/rules.d/70-persistent-net.rules`

```text
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{address}=="fa:16:3e:76:ec:a6", NAME="ens1"
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{address}=="fa:16:3e:f4:8d:87", NAME="ens2"
```


### Set the interface adapter file contents

Navigate to the network scripts directory and look for any existing script files. Show then remove
any old ones.

```bash
cd /etc/sysconfig/network-scripts
ls | grep "ifcfg-"
cat ifcfg-ens33
# remove the file
rm ifcfg-ens33
```

Generally in OpenStack, DHCP will be used. For an interface that uses DHCP, give it the following
contents - changing the `DEVICE` value as appropriate.

Be sure to include the mac address of the port in HWADDR.

```text
DEVICE=ens1
BOOTPROTO=dhcp
ONBOOT=yes
USERCTL=no
HWADDR=...
```

Often enough during a migration project, net-admins may extend their in-place layer 2 VLANs to the
OpenStack cloud. When that occurs, enabling OpenStack-managed DHCP is often not a good option,
and the prior static IP addresses should be preserved.

To define an interface with a static IP address, write it as follows:

```text
DEVICE=ens2
BOOTPROTO=none
ONBOOT=yes
USERCTL=no
PREFIX=24
IPADDR=192.168.0.123
HWADDR=...
# On the interface which acts as the default route, also add:
GATEWAY=192.168.0.1
DEFROUTE=yes
DNS1=192.168.0.2
DNS2=192.168.0.3
DOMAIN=domain.com
```


---


## Unmount/Release VM the volume(s)

The easiest way to unmount everything from the migration work is to simply shut it down. This will
also help avoid LVM-related problems.

```bash
openstack server stop <migration worker>
```

Next, remove the volumes from the worker

```
openstack server remove volume <server> <volume>
```


---


## Build a new VM

Examples showing how to set a specific IP address on the ports can be found at the end of the
[VMware migration](/vmware-migration.html) guide.
