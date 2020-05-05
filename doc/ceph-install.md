[Index](/)
\> Installing Ceph

# Installing Ceph

## About Ceph

[Ceph](https://ceph.io/) is Breqwatr's open-source storage solution of choice.

Ceph is an extremely scalable, cost effective, and feature-rich. Originally
created by Inktank which was later acquired and is now developed by Red Hat.
Ceph has been open source since its inception.

## Before you begin

Ensure that voidith is installed and the host from which it will run can SSH using a keypair as
root to each Ceph member node. Also ensure each member node has Python installed - Ansible needs
it.

## Install Procedure

### SSH Key

Identify the path of the SSH key that will be used to SSH to each server. Test it out now, SSH as
root to each server once. Connect by hostname to ensure your DNS or `/etc/hosts` are set up.

### Ansible Inventory

The inventory file defines which servers will own what roles in your cluster.
Each server listed in the inventory must have an entry in their
`/root/.ssh/authorized_keys` file and permit Ceph-Ansible to SSH as root.

For a summary of what each service does, check [Ceph's documentation](https://docs.ceph.com/docs/mimic/start/intro/).

Name this file `ceph-inventory.yml`.


{% gist de9ed062c773768c418da91e23733492 %}


### group\_vars directory

Create a directory named `group_vars`

```bash
mkdir -p group_vars
```

### all.yml

{% gist 3f30e1659a45fb3976654e1771fe5327 %}


### osds.yml

{% gist 6786866104c91fe95b9e802b23d43ccc %}
~



---


# Deploy Ceph


```bash
voidith ceph ceph-ansible \
  --inventory <path to inventory file> \
  --group-vars <path to group_vars directory> \
  --ssh-key <path to ssh private key file (usually id_rsa)>
```


## Double-check osd memory target

In the deployed servers hosting the OSD roles, check ceph.conf's
`osd memory target` value. Sometimes ceph-ansible picks a value that is WAY
too high. This is the ammount of ram **each** OSD service will use under high
load.

