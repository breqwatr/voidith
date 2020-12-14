[Back to the migration guide](/vmware-migration.html)


# Booting the OpenStack Server

Once the volume has been converted from VMware to KVM, a server can boot from it.

If you're uncertain about the `server create` syntax, check
[the official documentation](https://docs.openstack.org/python-openstackclient/train/cli/command-objects/server.html).


## Remove volumes from migration workers

If the volumes are still attached to a Windows/Linux migration worker, remove them.

```bash
openstack server remove volume <migration worker server> <volume>
```


## Determine which flavor to use

```bash
# Determine the RAM & CPU requirements
voithos vmware show-vm -n <vm name>
openstack flavor list
```


## Identify the ports that were created for this VM

```bash
openstack port list

# if you know the name:
openstack port list | grep <name>
```


## Identify the volumes that were created for this VM

```bash
openstack volume list

# or if you know the name
openstacl volume list | grep <name>
```


## Create the server

Notes:

- Second, third, etc volumes follow a convention as follows:
    - `--block-device-mapping vdb=server-vol-2`
    - `--block-device-mapping vdc=server-vol-3`
- Each port is attached with `--nic port-id=<port id>`, which can be used multiple times

```bash
openstack server create \
  --volume <boot volume>
  --nic port-id=<port id> \
  --block-device-mapping vdb=server-vol-2
  --flavor <flavor>
  <name>
```
