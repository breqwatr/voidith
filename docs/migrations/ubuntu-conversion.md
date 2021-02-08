[Back to the migration guide](/vmware-migration.html)


# Converting Ubuntu VMs from VMware to OpenStack

## Requirements

Before this guide can be followed:

 - The virtual volumes of the VM must have already been imported into Cinder
 - The Linux migration worker VM must be online and have the newly imported cinder volumes attached
 - If the volumes use LVM, ensure the volumes can be seen in `lvdisplay`.
 - The OpenStack Neutron ports that this VM will use have been created.
   Their MAC addresses will be used to configure the VM's interface files.

---

## Determine the boot mode (UEFI/BIOS)

If the system is configured to boot with UEFI, `--image-property hw_firmware_type=uefi` must be
set on the boot volume in OpenStack. You can tell this was missed if the VM tries to PXE then fails
and throws an error about not finding its boot device.

Show the boot mode:

```bash
voithos migrate ubuntu get-boot-mode <device>

# If the return value is "UEFI", you will eventually need to execute:
openstack volume set --image-property hw_firmware_type=uefi <volume>
```


## (optional) Repair the file-systems

Often a system will benefit from having its volumes repaired. Voithos can run `fsck` and
`xfs-repair` on those volumes while their mounted. Sometimes this is required for the migrated VM
to boot. If the VM had multiple drives, specify each.

```bash
# If fsck says it failed, try re-running it
voithos migrate ubuntu repair-partitions <device> <device> <device...>
```


## Mount the VM's partitions

Specify each connected device of the migration target VM. The automation will find its root volume,
parse `/etc/fstab` on it, and set up the mounts so you can `chroot` into it.

```bash
voithos migrate ubuntu mount <device> <device> <device...>
```


## Remove installed software

Voithos can remove certain problem packages from the migration target:

- VMware tools shouldn't hurt anything on KVM/OpenStack, but we don't need it
- cloud-init is nice to have in templates. It causes all sorts of problems during migrations

```bash
voithos migrate ubuntu uninstall vmware-tools
voithos migrate ubuntu uninstall cloud-init
```


## Configure Networking

The network interface names in Linux  usually change during a migration, and it can be
difficult to predict what the new ones will be. Voithos will inject `udev` rules into the boot
volume to enforce the names, and write interface files accordingly. This is the `udev` same
procedure in Ubuntu as it is in RedHat.

- Interface names are commonly `ens0`, `ens1`, `ens2`, and so on.
- Prefix is the CIDR prefix. For `255.255.255.0`, the prefix is `24`.
- Reference: [Consistent network device naming](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/networking_guide/ch-consistent_network_device_naming)

```bash
# Example of setting a DHCP interface
voithos migrate ubuntu set-interface <device> --name <interface name> --dhcp --mac "<mac address>"

# Setting a static interface with default route and DNS settings.
# --gateway, --dns, and --domain are all optional
voithos migrate ubuntu set-interface \
  --name <interface name> \
  --static \
  --mac "<mac address>" \
  --ip-addr "<ip address>" \
  --prefix <prefix> \
  --gateway <ip address> \
  --dns <first dns server> \
  --dns <another dns server> \
  --domain "<dns search domain>"
```

Optionally, you might want to navigate to either `/convert/root/etc/network/interfaces/` or
`/convert/root/etc/netplan/` and clean up the previous interface configs. They won't hurt anything,
but doing so would result in a "cleaner" import/conversion.


## Unmount/Release VM the volume(s)

This will remove all of the mounted volumes.

```bash
voithos migrate ubuntu unmount
```

## Shutdown the migration server

The LVM's won't clean themselves up nicely between migrations.

```bash
openstack server stop <migration worker>
```

## Remove the volumes from the worker

```
openstack server remove volume <server> <volume>
```
