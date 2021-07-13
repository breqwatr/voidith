# Installing Ceph

## About Ceph

[Ceph](https://ceph.io/) is Breqwatr's open-source storage solution of choice.

Ceph is extremely scalable, cost effective, and feature-rich. Originally
created by Inktank,then acquired by Red Hat. Ceph has been open source since its inception.

## Before you begin

- Install Python on each ceph node. If convenient, also install `voithos`.


## Install Procedure

### Zap Disks

Unless the disks to be used for OSDs are brand new, you need to clear the first few blocks of data
off each one.

If it's easy to install voithos on the OSD nodes, you can use use `voithos ceph zap-disk`.

If not, `voithos ceph zap-disk` just wraps the following to commands:

```bash
disk=... # set the drive name... Careful not to overwrite your boot drive!
wipefs -a $disk
dd if=/dev/zero of=$disk bs=4096k count=100
```


### SSH Key

Identify the path of the SSH key that will be used to SSH to each server. Test it out now, SSH as
root to each server once. Connect by hostname to ensure your DNS or `/etc/hosts` are set up.

### Ansible Inventory

The inventory file defines which servers will own what roles in your cluster.
Each server listed in the inventory must have an entry in their
`/root/.ssh/authorized_keys` file and permit Ceph-Ansible to SSH as root.

For a summary of what each service does, check [Ceph's documentation](https://docs.ceph.com/en/latest/).

Name this file `ceph-inventory.yml`.


{% gist de9ed062c773768c418da91e23733492 %}


### group\_vars directory

Create a directory named `group_vars`

```bash
mkdir -p group_vars
```

### all.yml

{% gist 3f30e1659a45fb3976654e1771fe5327 %}

Note: If you've manually installed `docker-ce` to use the ceph node as a deployment server, you
need to put `container_package_name: docker-ce` in this file.

In newer releases, if you'll be installing OpenStack too, disable Grafana so it doesn't cause a
conflict:

```yml
dashboard_enabled: False
```


### osds.yml

{% gist 6786866104c91fe95b9e802b23d43ccc %}
~



---


# Deploy Ceph


```bash
voithos ceph ceph-ansible \
  --inventory <path to inventory file> \
  --group-vars <path to group_vars directory> \
  --ssh-key <path to ssh private key file (usually id_rsa) \
  -r (ceph release)
```


## Double-check osd memory target

In the deployed servers hosting the OSD roles, check ceph.conf's
`osd memory target` value. Sometimes ceph-ansible picks a value that is WAY
too high. This is the amount of ram **each** OSD service will use under high
load.



---

# Optional - update CRUSH rules

If this is a single-node deployment but you still want 2 replicas for data availability, you need
to change the `chooseleaf_firstn` CRUSH rule from `host` to `osd`

From a ceph monitor node export the crushmap to a text file

```bash
ceph osd getcrushmap -o crushmap.bin
crushtool --decompile crushmap.bin  -o crushmap.txt
```
Replace `step chooseleaf firstn 0 type host` with `step chooseleaf firstn 0 type osd`.

Apply the changes

```bash
crushtool --compile crushmap.txt  -o new.crushmap.bin
ceph osd setcrushmap -i new.crushmap.bin
```

