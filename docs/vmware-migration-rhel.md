# Migrating RedHat Linux from VMware


## Requirements

Before this guide can be followed, it is expected that the virtual volumes of the VM have already
been imported into Cinder. If that hasn't been done yet, follow [this guide](/vmware-migration.html)
first.

Also the migration worker VM must be online and have the newly imported cinder volumes attached.
If the volumes use LVM, ensure the volumes can be seen in `lvdisplay`.


---


## Adding Virtio drivers to initrd files

In many releases of RedHat, the VM will boot to dracut when imported into OpenStack unless you
manually inject the Virtio drivers to the initrd files.


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

Optionally, `fsck` the partition while you're in the neighbourhood. It can be a good idea to do this
against each partition while they're mounted here, you won't have a better opportunity.

```bash
# show the filesystem
blkid /dev/mapper/cl-root
# in this case it's xfs
xfs_repair /dev/mapper/cl-root
```

Mount the root volume. Use the device-mapper path in your `mount` command.

```
mkdir -p /mnt/root
mount /dev/mapper/cl-root
```

Take a look at the `/etc/fstab` file of this VM. If it mounts other LV's or partitions, mount them
into `/mnt` on your worker VM too. They'll be bind-mounted into the root volume in the next step.
Don't worry about any swap mounts.

```bash
cat /mnt/root/etc/fstab
```


### Bind-mount to the root volume

Bind-mount the boot volume and system devices into the folder where the root partition was mounted.

```bash
mount --bind /mnt/boot /mnt/root/boot
for x in sys proc run dev; do mount --bind /$x /mnt/root/$x; done
# Also --bind mount any other LVs/partitions that fstab mentioned
```


### Install the virtio drivers

Change root into the mounted root partition:

```bash
cd /mnt
chroot root bash
```

Get the Kernel version. The initrd files will have the same version. Use it to add the drivers
by calling `dracut` command.

```bash
# Get the version
version=$(rpm -q kernel --queryformat "%{VERSION}-%{RELEASE}.%{ARCH}\n" | sort -V | head -n 1)
# Check if the drivers are already installed
filename="/boot/initramfs-$version.img"
lsinitrd $filename | grep virtio
# If nothing is returned ("$?" == "1") then add the drivers with dracut
dracut -f $filename $version --add-drivers "virtio_pci virtio_blk virtio_net"
# Note: sometimes you'll see "dracut: FAILED ....". Check if it worked anyways, often it did
# confirm they're there now
lsinitrd $filename | grep virtio
```

The kernel driver files should appear in the final `lsinitrd` command output.


---


## Remove Installed software

From inside the `chroot` entered while installing the virtio drivers:


### Removing VMWare Tools

VMware tools shouldn't hurt anything on KVM/OpenStack, but we don't need it either.

```bash
rpm -qa | grep "vm-tools" | while read pkg; do echo "removing $pkg"; rpm -e $pkg; done
```


### Removing Cloud-Init

Sometimes cloud-init will already be installed in a VM. While generally nice to have, it causes all
sorts of problems during migrations. Usually it's best to simply remove it:

```bash
rpm -qa | grep cloud-init | while read pkg; do echo "removing $pkg"; rpm -e $pkg; done
```


---


## Configure Networking


### Disable consistent network device naming

The network adapters will probably change their names when they move to the new cloud.
RedHat has a concept of
"[consistent network device naming](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/networking_guide/ch-consistent_network_device_naming)"
which makes things rather complicated. Its best to just turn that feature off.

Check for any udev rules calling `rename_device`:

```bash
grep -ire "rename_device" /usr/lib/udev/rules.d/
```

If you find any entries, most commonly `/usr/lib/udev/rules.d/60-net.rules`, either edit the
file to disable the rule or simply delete the file:

```bash
rm -f /usr/lib/udev/rules.d/60-net.rules
```


### Set the interface adapter file contents

With the consistent naming feature disabled, the interfaces will name themselves eth0, eth1, and so
on. In the source VM the interfaces are often names something along the likes of `ens33`.

Navigate to the network scripts directory and look for any existing script files. If you see one,
print it.

```bash
cd /etc/sysconfig/network-scripts
ls | grep "ifcfg-"
cat ifcfg-ens33
# remove the file
rm ifcfg-ens33
```

Remove any old interface files, keeping in mind which ones said what. When you add new interfaces
to the server, the interface names will increment from `eth0` to `eth1` to `eth2` and so on in the
order which they're added. Write new interface files using the new names.

Generally in OpenStack, DHCP will be used. For an interface that uses DHCP, give it the following
contents - changing the `DEVICE` value as appropriate.

```text
DEVICE=eth0
BOOTPROTO=dhcp
ONBOOT=yes
USERCTL=no
```

Often enough during a migration project, net-admins may extend their in-place layer 2 VLANs to the
OpenStack cloud. When that occurs, enabling OpenStack-managed DHCP is often not a good option,
and the prior static IP addresses should be preserved.

To define an interface with a static IP address, write it as follows:

```text
DEVICE=eth1
BOOTPROTO=none
ONBOOT=yes
USERCTL=no
PREFIX=24
IPADDR=192.168.0.123
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
