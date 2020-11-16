# OpenStack
# Online Install with LVM Storage

This deployment model uses storage nodes that carve out volumes using LVM and present them using
iSCSI. These are ideally dedicated storage nodes, but can also be hyperconverged.

## Prepare LVM

1. [**Create the LVM volume group**](/openstack-lvm.html)


## Install OpenStack

1. (optional) Deploy a local Docker registry
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


## Arcus Configurations

Arcus is Breqwatr's OpenStack self-service web portal.

- [**Install Arcus**](/arcus-install.html)

To collect pricing data correctly, Arcus requires a particular default archive policy be set.

- [**Configure default metering archive policy**](/openstack-gnocchi-config.html)


## Monitoring

Breqwatr's OpenStack setup supports containerized monitoring tools to watch the OpenStack servers.

- [**Install Prometheus and Grafana**](/grafana-prometheus-config.html)
- [**Configure Graphs and Alerts**](/grafana-graphs-alerts.html)
- [**Configure Kibana**](/kibana-setup.html)
