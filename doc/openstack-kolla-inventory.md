[Index](/)
\> Creating Kolla-Ansible's Inventory File

# Creating Kolla-Ansible's Inventory File

The inventory file defines which nodes will run what OpenStack roles.

Generate a template of the file. Kolla-Ansible's git checkout contains sample
inventory files. Voidith can automatically extract one of those sample files
to the present working directory. The inventory files change from OpenStack
release to OpenStack release, so be sure to use the correct `--release` option.


```bash
# creates ./inventory
voidith openstack get-inventory-template --release stein
```

This is a standard [INI-format](https://en.wikipedia.org/wiki/INI_file) Ansible
[inventory file](https://docs.ansible.com/ansible/2.3/intro_inventory.html).
While helpful, it isn't necessary to be familiar with Ansible to edit the
 inventory file.

OpenStack roles are represented as follows:

```ini
[<role>]
<hostname>      <additional properties>

# example
[control]
localhost       ansible_connection=local
```


Edit the template to list each hostname under each role it will operate.
In small clusters, you can list the same few nodes for each role and it will
work just fine. Larger clusters benefit from increased segregation of
responsibilities.

No additional properties (such as `ansible_connection=local`) are required.

In general, only the contro, network, compute, storage, and monitoring sections
need to be populated.

```ini
[control]
controlNode1
controlNode2
controlNode3

[network]
controlNode1
controlNode2
controlNode3

[compute]
computeNode1
computeNode2
computeNode3
computeNode4
computeNode5

[storage]
storageNode1
storageNode2
storageNode3

[monitoring]
controlNode1
controlNode2
controlNode3
```

In the deployment server, now's a good time to double-check that you can
ping each of those hostnames. The deployment will fail if your DNS or
`/etc/hosts` file aren't set up correctly.

Similarly, SSH to each server using your designated SSH key as root to
confirm that the `authorized_keys` files are deployed correctly.
