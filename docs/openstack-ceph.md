# OpenStack Ceph Setup

As is documented in the [OpenStack Installation](/openstack-install.html) page,
a `config/` directory can be created to modify the OpenStack service
configuration files.

The `config/` directory will be used to deploy:

- `ceph.conf`: Ceph's config files
- `ceph.client.<service>.keyring`: Ceph's authentication keyring files
- `cinder.conf` and `glance-api.conf`: OpenStack service configuration
  overrides.


## Creating ceph.conf configuration files

### Gather information from Ceph monitor nodes

On a Ceph monitor node, collect some values from `/etc/ceph/ceph.conf`.

```bash
# Show the ceph.conf file's values
cat /etc/ceph/ceph.conf | grep -e fsid -e "mon initial members" -e "mon host"
```

### Write the OpenStack service ceph.conf files

The following files will be created:

- `config/cinder/ceph.conf`
- `config/nova/ceph.conf`
- `config/glance/ceph.conf`
- `config/gnocchi/ceph.conf`

On the deployment server, create the directories. Remember that this `config/`
directory might be used for other things too - use the same directory for
everything.

```bash
mkdir -p config/cinder/cinder-volume
mkdir -p config/nova
mkdir -p config/glance
mkdir -p config/gnocchi
```

Create the four `ceph.conf` files.

Each file will be similar, except that the `keyring =` line differs. For the
keyring line, replace `<service>` with either cinder, nova, gnocchi, or glance in
accordance with which file you're editing.

```
[global]
fsid = <fsid from monitor's ceph.conf>
mon initial members = <mon_initial_members from monitor's ceph.conf>
mon host = <mon_host from monitor's ceph.conf>
auth cluster required = cephx
auth service required = cephx
auth client required = cephx
keyring = /etc/ceph/ceph.client.<service>.keyring
rbd default features = 3
```

**Note**: If the value of `mon host` in ceph.conf on the monitor
nodes looks like this `mon host = [v2:192.168.0.13:3300,v1:192.168.0.13:6789]`,
it's using a newer syntax that isn't backwards compatible. Cinder's ceph
client cannot parse the new format. Instead, use the old format - a space
delimited list of each monitor node's IP address with no ports for ceph.conf under 
cinder, glance and nova.
Example:
`mon host = 192.168.0.13 192.168.0.14 192.168.0.15`
This change isn't applicable for gnocchi's ceph.conf, use the newer format for that.
Example:
`mon host = [v2:192.168.0.13:3300,v1:192.168.0.13:6789]`

## Creating ceph.client.\<service\>.keyring files

### Creating CephX Keys

CephX keys are required on OpenStack's Cinder, Nova, Gnocchi, and Glance services to
interact with a secure Ceph cluster. These keys are created using the `ceph`
command-line. They can later be piped to files for use with Kolla-Ansible.
First check the current keyrings by running:
```bash
ceph auth ls
```

### Create new keys

Create keys for Cinder, Glance, and Nova. Grant them the capabilities required
for OpenStack against the volumes and images pools.

```bash
ceph auth get-or-create client.glance
ceph auth caps client.glance \
  mon 'allow r' \
  mds 'allow r' \
  osd 'allow rwx pool=volumes, allow rwx pool=images, allow rwx pool=gnocchi, allow class-read object_prefix rbd_children'

ceph auth get-or-create client.cinder
ceph auth caps client.cinder\
  mon 'allow r' \
  mds 'allow r' \
  osd 'allow rwx pool=volumes, allow rwx pool=images, allow rwx pool=gnocchi, allow class-read object_prefix rbd_children'

ceph auth get-or-create client.nova
ceph auth caps client.nova \
  mon 'allow r' \
  mds 'allow r' \
  osd 'allow rwx pool=volumes, allow rwx pool=images, allow rwx pool=gnocchi, allow class-read object_prefix rbd_children'

ceph auth get-or-create client.gnocchi
ceph auth caps client.gnocchi \
  mon 'allow r' \
  mds 'allow r' \
  osd 'allow rwx pool=volumes, allow rwx pool=images, allow rwx pool=gnocchi, allow class-read object_prefix rbd_children'
```

### Gather information from Ceph monitor nodes

On the Ceph monitor nodes, print the cinder, glance, gnocchi, and nova keyring text.

```bash
ceph auth get client.cinder 2>/dev/null
ceph auth get client.nova   2>/dev/null
ceph auth get client.glance 2>/dev/null
ceph auth get client.gnocchi 2>/dev/null
```

The keyrings will look like this, with the keyring name at the top and the
`key =` line varying by key.

```
[client.cinder]
        key = AQAIS59eT5mABhAAmQ4+CBIRaGGRlEVCPbWdFw==
        caps mds = "allow r"
        caps mon = "allow r"
        caps osd = "allow rwx pool=volumes, allow rwx pool=images, allow class-read object_prefix rbd_children"
```

### Create the keyring files

It's easiest to just create the 4 keyring files, then distribute them to the
various locations they need to reside for the automation to find them.

The four files are:

- `ceph.client.cinder.keyring`
- `ceph.client.nova.keyring`
- `ceph.client.glance.keyring`
- `ceph.client.gnocchi.keyring`

Populate each of those files with the output from the above `ceph auth get`
commands, then copy them into the following paths:

- `config/cinder/ceph.client.cinder.keyring`
- `config/cinder/cinder-volume/ceph.client.cinder.keyring`
- `config/nova/ceph.client.cinder.keyring`
- `config/nova/ceph.client.nova.keyring`
- `config/glance/ceph.client.glance.keyring`
- `config/gnocchi/ceph.client.gnocchi.keyring`

## Creating OpenStack config files

OpenStack needs to be configured to use Ceph. The following files are required:

- `config/cinder.conf`
- `config/glance/glance-api.conf`


### config/cinder.conf

During the [OpenStack Installation](/openstack-install.html), a `passwords.yml`
file was generated. This file contains the value that will be used for
`rbd_secret_uuid` in `cinder.conf`.

```bash
cat passwords.yml | grep cinder_rbd_secret_uuid | awk '{print $2}'
```

OpenStack Cinder allows the configuration of backends - the mechanisms by which
logical block devices are carved out. We typically name our Ceph backend
Breqwatr. Insert your chosen backend name for `enabled_backends`,
`default_volume_type`, the section header in square brackets, and
`volume_backend_name`.

Note that "volume type" and "backend" are not exactly the same thing, but a
Cinder volume type with the same name will be created later.


```
[DEFAULT]
enabled_backends=<backend name>
default_volume_type=<backend name>

[<backend name>]
rbd_ceph_conf=/etc/ceph/ceph.conf
rbd_user=cinder
backend_host=rbd:volumes
rbd_pool=volumes
volume_backend_name=<backend name>
volume_driver=cinder.volume.drivers.rbd.RBDDriver
rbd_secret_uuid = <uuid from passwords.yml>
```


### config/glance/glance-api.conf

The glance config file always has the same content:

```
[DEFAULT]
show_image_direct_url = True

[glance_store]
stores = glance.store.rbd.Store
default_store = rbd
rbd_store_pool = images
rbd_store_user = glance
rbd_store_ceph_conf = /etc/ceph/ceph.conf
```

---

No other Ceph-related configuration is required.

Before you continue, double-check that (at minimum) the following files exist:

`find .`

```text
./passwords.yml
./config
./config/gnocchi
./config/gnocchi/ceph.conf
./config/gnocchi/ceph.client.gnocchi.keyring
./config/glance
./config/glance/ceph.conf
./config/glance/ceph.client.glance.keyring
./config/glance/glance-api.conf
./config/cinder
./config/cinder/ceph.conf
./config/cinder/cinder-volume
./config/cinder/cinder-volume/ceph.client.cinder.keyring
./config/cinder/ceph.client.cinder.keyring
./config/cinder.conf
./config/nova
./config/nova/ceph.conf
./config/nova/ceph.client.cinder.keyring
./config/nova/ceph.client.nova.keyring
```
