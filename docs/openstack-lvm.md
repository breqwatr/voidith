# OpenStack LVM Storage Setup

## Create LVM Volume Group

Choose a volume group name. By default, we use `cinder-volumes`.

Configure the volume group on each OpenStack cinder-volume node.

```bash
# List your drives
fdisk -l

# Identify the drive to be used. Example: /dev/sdb

# Create a phsical volume in LVM
pvcreate /dev/sdb

# Confirm the physical volume was created by listing them
pvdisplay

# Create the volume group
vgcreate cinder-volumes /dev/sdb

# Confirm the volume group was created
vgdisplay
```

Later, after volumes for VMs have been created, you can see them in LVM as
logical volumes.

```bash
lvdisplay cinder-volumes
```

