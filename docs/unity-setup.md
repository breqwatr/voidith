# Unity Storage for OpenStack Setup

## Cinder Setup

To configure OpenStack Cinder for use with Unity Storage, create a `cinder.conf` file in the
`config/cinder/` directory with contents as follows.

Be sure to replace anything with `<example>` angle brackets with your own values.

The `volume_backend_name` defined here will be used as a property when creating the OpenStack
volume type (`--property volume_backend_name=<volume_backend_name>`).


`vi config/cinder/cinder.conf`

```ini
[DEFAULT]
enabled_backends = <volume backend name>

[<volume backend name>]
storage_protocol = iSCSI
san_ip = <unity iscsi VIP>
san_login = <iscsi service account username>
san_password = <iscsi service account password>
volume_driver = cinder.volume.drivers.dell_emc.unity.Driver
volume_backend_name = <volume_backend_name>
unity_storage_pool_names = <unity pool name>
```

## Glance Setup

### Image-Volume Cache

Creating VMs can be slow using iSCSI storage. Unlike with Ceph, with iSCSI  OpenStack will download
the Glance image to the host and then dd it into a new empty volume each time it makes a new
image-backed volume.

Once the cloud is deployed, you can update the `cinder-volume.conf` file with an OpenStack service
account and project to created cached volumes, a feature supported by Unity storage. This will
slightly slow the creation of a volume based on a Glance image the first time it is created, then
greatly speed up all subsequent volumes from that same image.

Collect the following:

- `cinder_internal_tenant_project_id`: The UUID of a service-account project for the image-volume
  cache.
- `cinder_internal_tenant_user_id`: The UUID of a service-account user for the image-volume cache.

Add the above two values to the `[DEFAULT]` section of `cinder-volume.conf` and add a line saying
`image_volume_cache_enabled = True` to the `[<volume backend name>]` section of that same file.


### Example

```ini
[DEFAULT]
enabled_backends = <volume backend name>
cinder_internal_tenant_project_id = <project id>
cinder_internal_tenant_user_id = <user id>

[<volume backend name>]
storage_protocol = iSCSI
san_ip = <unity iscsi VIP>
san_login = <iscsi service account username>
san_password = <iscsi service account password>
volume_driver = cinder.volume.drivers.dell_emc.unity.Driver
volume_backend_name = <volume_backend_name>
unity_storage_pool_names = <unity pool name>
image_volume_cache_enabled = True
```


### NFS-Backed Glance

Another issue with iSCSI-backed storage is that glance must store its images as files. This tends
to totally fill the drives of the Glance API nodes rather quickly. To work past this issue, we
suggest you create a NFS share on your Unity storage and present it to the Glance API container.

#### Create an NFS share in Unity

1. Log into the unity web UI
1. Navigate to storage > file
1. Click on NAS servers
1. Create a NAS server. It can use the same interfaces as iSCSI but it needs unique IP addresses
1. Modify the NAS to ensure it has two NICs, two IPs.
1. Navigate to File Systems at the top and make a filesystem on this NAS. During the wizard, check off the NFS option and give it a name such as “glance”.
1. Authenticate your glance servers. If they aren’t added yet, you can add them in the hosts section.
1. The share should now show up in the NFS tab.

#### Mount the shares to the glance host

Install nfs-common if it isn't already present.

```bash
apt-get install nfs-common
```

Add the NFS entries in `/etc/fstab`:
```
10.1.0.24:/glance1 /nfs/glance-1 nfs
10.1.0.25:/glance1 /nfs/glance-2 nfs
```


#### Set the permissions

Glance in Kolla's Docker image has a user ID of 42415.

```bash
chown -R 42415:42415 /nfs/glance-1
chmod 775 /nfs/glance-1/images
```

#### Configure Glance to mount the volumes

Add the following to your `globals.yml`:

```
glance_extra_volumes:
  - "/nfs/glance-1:/glance-1"
  - "/nfs/glance-2:/glance-2"
```

#### Make Glance use the mounted volumes for its images

Glance supports a configuration named `filesystem_store_datadirs` in its glance.conf file.
It’s documented [here](https://docs.openstack.org/glance/latest/configuration/configuring.html).
Basically you can list that config item twice, with :100 and :200 at the end of each.
The higher number will be used first. By this mechanism we can have redundancy.

`vi config/glance/glance-api.conf`

```
[DEFAULT]
enabled_backends = nfs_backend:file

[glance_store]
default_backend = nfs_backend

[nfs_backend]
filesystem_store_datadir=
filesystem_store_datadirs = /glance-1:100
filesystem_store_datadirs = /glance-2:200
store_description = "Shared filesystem store"
```

**Note**: Don't forget to increase the Nova local disk reservation accordingly if you're colocating
Glance with a Nova compute node. If you have a 200GB NFS share, set asside 400GB extra on the host,
as Nova will see each mount point as a distinct volume that it might use for ephemeral disks.


---

# Multipath configuration

If you intend to use Multipath with the Unity iSCSI, this section needs to be executed too.


## globals.yml

```yaml
enable_multipathd: yes
```

## Nova config file

Enable multipath in Nova Compute's configuration file.

`vi config/nova/nova-compute.conf`

```ini
[libvirt]
volume_use_multipath = True
```
