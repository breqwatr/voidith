# Voithos Qemu-Img

The `qemu-img` command is the industry standard tool for operating on virtual data volumes.
Voithos strives to require only itself, its python packages, and Docker to provide all of its
features. As such, Breqwatr has packages the `qemu-img` command into an
[image on Docker Hub](https://hub.docker.com/r/breqwatr/qemu-img). Qemu-img is also easily
installed on Ubuntu using `apt-get install qemu-utils`.

The following examples use Voithos, but don't neccesarily require it. To run them without Voithos,
simply omit `voithos util` at the start of the command. We've gone for parity with the original
syntax.


## Show raw size of virtual disk file

A thin provisioned virtual disk, such as a `.qcow2` file or `.vmdk` file, will often require much
more space when converting it to `raw` format or mapping it to a block device. To show the raw size
of the volume, run:

```bash
voithos util qemu-img info <file>
```

The `virtual size:` listed is the raw size.


## Write a file to a block device

The `qemu-img convert` command can copy the contents `vmdk`, `vhd`, or `qcow2` into Cinder-managed
block devices. Connect the device to a VM which holds the volume file, and find its device path
in `fdisk`. For example, `/dev/vdb`.

Be sure that the size of the block device is at least the `virtual size` shown in the output from
the `qemu-img info` command.

When writing to a block device, always set the output format `-O` to `raw`:

```bash
voithos util qemu-img info <disk file>

# Example:
voithos util qemu-img convert -f vmdk -O raw test-centos-1-1.vmdk /dev/vdb
```

If the disk had any partitions on it, you'll see them now with `fdisk -l`.

To see any new LVM volumes, run:

```bash
partprobe
pvscan
lvdisplay
```
