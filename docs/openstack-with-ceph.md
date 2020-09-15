# OpenStack
# Online Install with Ceph Storage

This installation procedure is our most common use-case. It requires that
Ceph already be installed. If you haven't installed Ceph yet, follow the
[Ceph install guide](/ceph-install.html) first.


## Prepare Ceph

1. [**Create Ceph OSD pools for OpenStack**](/ceph-pools.html)
1. [**Create Ceph keyring, ceph.conf, glance-api.conf and cinder-volume.conf files**](/openstack-ceph.html)

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
1. [**Update Chrony config file**](/update-chrony-config-file.html) - `chrony/config.json`
1. [**Generate the admin OpenRC file**](/openstack-kolla-admin-openrc.html) - `admin-openrc.sh`


## Arcus Configurations

Arcus is Breqwatrs OpenStack self-service portal.

- [**Install Arcus**](/arcus-install.html)

To collect pricing data correctly, Arcus requires a particular default archive policy be set.

- [**Configure default metering archive policy**](/openstack-gnocchi-config.html)

Arcus can be integrated with Ceph to enable additional functionality such as reporting and in-place
snapshot restores.

- [**Integrate Arcus with Ceph**](/arcus-ceph-integration.html)


## Monitoring

Breqwatr's OpenStack setup supports containerized monitoring tools to watch the OpenStack servers.

- [**Install Prometheus and Grafana**](/grafana-prometheus-config.html)
- [**Configure Graphs and Alerts**](/grafana-graphs-alerts.html)
