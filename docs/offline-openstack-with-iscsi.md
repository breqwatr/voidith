# OpenStack
# Offline Install with iSCSI Storage

This deployment model uses storage nodes that carve out volumes using LVM and present them using
iSCSI. These are ideally dedicated storage nodes, but can also be hyperconverged.

## Prepare iSCSI

Depending on the storage backend you're using, the procedure varies.

- [**Unity Storage iSCSI Cinder Configuration**](/unity-setup.html)

## Install OpenStack

1. [**Deploy a local Apt service**](/apt.html)
1. [**Deploy a local Pip service**](/pip.html)
1. Deploy a local Docker registry
   - [**Launch a local Docker registry**](/registry.html) and
   - [**Sync Kolla images to it**](/openstack-registry-mirror.html)
1. [**Prepare the metal cloud servers**](/openstack-server-setup.html)
1. [**Generate unique passwords for OpenStack service**](/openstack-kolla-passwords.html) -
   `passwords.yml`
1. [**Create globals.yml for Kolla-Ansible**](/openstack-kolla-globals.html) - `globals.yml`
1. [**Write the inventory file for Kolla-Ansible**](/openstack-kolla-inventory.html) - `inventory`
1. [**Collect or generate HTTPS certificates**](/openstack-kolla-certificates.md) - `certificates/`
1. [**Write Kolla-Ansible's config/ files**](/openstack-kolla-config.html) - `config/`
1. [**Bootstrap the OpenStack servers**](/openstack-kolla-bootstrap.html)
1. [**Pull Docker images to each node**](/openstack-kolla-pull.html)
1. [**Initialize OpenStack's service containers**](/openstack-kolla-deploy.html)
1. [**Generate the admin OpenRC file**](/openstack-kolla-admin-openrc.html) - `admin-openrc.sh`
1. [**Configure default archive policy**](/openstack-gnocchi-config.html) - `usage and metering`
1. [**Run the smoke-tests**](/openstack-smoke-tests.html)
