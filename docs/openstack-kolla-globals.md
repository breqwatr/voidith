# Kolla-Ansible Globals.yml

Writing the `globals.yml` file is the most complicated step when deploying OpenStack. This page
covers the options Breqwatr generally chooses. Combine everything that would apply to your
deployment into one `globals.yml` file.

This information is accurate for the Train release of OpenStack.
When in doubt, check the [official globals.yml template on GitHub](https://github.com/openstack/kolla-ansible/blob/stable/train/etc/kolla/globals.yml)
for your release.

## Docker & Image config

```yaml
# prefix for image names (breqwatr/<image>)
docker_namespace: breqwatr

# Offline install settings.
# Keep docker_apt_key_id empty
docker_apt_key_id:
docker_apt_url:  "http://<apt url with port>"
docker_apt_repo: "deb [trusted=yes arch=amd64] <docker_apt_url> <ubuntu-release> stable"
docker_apt_package: "docker-ce=5:19.03.12~3-0~ubuntu-bionic"

# openstack release
openstack_release: train

# These are always going to be the same - we build all images as ubuntu-source
kolla_base_distro: ubuntu
kolla_install_type: source

# Optionally, define a local registry
#docker_registry:
#docker_registry_insecure: "{{ 'yes' if docker_registry else 'no' }}"
#docker_registry_username:
#docker_registry_password: <set in the passwords.yml file>
```

## Interface Config

*Reminder*: Neutron needs a dedicated interface. If you give that interface VLAN sub-interfaces,
they’ll work but Neutron won’t be able to use those VLANs. Neutron won’t error out when you try
, they just won’t work.

```yaml
neutron_external_interface: eno2
```

You’ll usually just configure one interface (a bond) for everything “undercloud” as follows:

```yaml
network_interface: eno1
```

For more fine-grained control, look into these  options. They’re explained well
[here](https://github.com/openstack/kolla-ansible/blob/cd3c51197e04d9df5077dcb92e8521efca5e5075/doc/source/admin/production-architecture-guide.rst).

```yaml
#kolla_external_vip_interface: "{{ network_interface }}"
#api_interface: "{{ network_interface }}"
#storage_interface: "{{ network_interface }}"
#cluster_interface: "{{ network_interface }}"
#swift_storage_interface: "{{ storage_interface }}"
#swift_replication_interface: "{{ swift_storage_interface }}"
#tunnel_interface: "{{ network_interface }}"
#dns_interface: "{{ network_interface }}"
#octavia_network_interface: "{{ api_interface }}"
```

## HAProxy

```yaml
enable_haproxy: yes

# Matching internal VIP and external VIP don't work correctly with HTTPS enabled
kolla_same_external_internal_vip: no
kolla_internal_vip_address: <internal vip>
kolla_external_vip_address: <external vip>

kolla_external_fqdn: < external VIP or fqdn>

kolla_enable_tls_internal: no
kolla_enable_tls_external: yes
```

## KeepAlived

It's important to choose a unique VRID on your subnet.

```yaml
enable_keepalived: yes
keepalived_virtual_router_id: <1 to 255>
```

## MariaDB


```yaml
enable_mariadb: yes

```


## Memcached

```yaml
enable_memcached: yes
```


## RabbitMQ

```yaml
enable_rabbitmq: yes
```

## Chrony

```yaml
enable_chrony: yes
```

## Fluentd

```yaml
enable_fluentd: yes
```

## Ceph

While possible, we never use Kolla-Ansible to install Ceph. Instead we prefer Ceph-Ansible.

```yaml
enable_ceph: no
```

## Keystone

```yaml
enable_keystone: yes

keystone_admin_user: admin
keystone_admin_project: admin
```

## Nova

```yaml
enable_nova: yes
enable_nova_ssh: yes

# Compute type is "kvm" for metal, "qemu" when running OpenStack in a VM
nova_compute_virt_type: kvm

#nova_backend_ceph: no
```

## Placement

```yaml
enable_placement: yes
```

## Neutron

```yaml
enable_neutron: yes
enable_neutron_provider_networks: yes
neutron_extension_drivers:
  - name: port_security
    enabled: true
  - name: dns
    enabled: true
```

## Glance

```yaml
enable_glance: yes

#glance_backend_ceph: no
#glance_backend_file: yes

# This isn't useful with Ceph but can be useful for iscsi storage appliances
# We haven't tested it, don't use it in production yet
#enable_glance_image_cache: no
```

## Cinder

Don’t use both Ceph and LVM backends at the same time.


```yaml
enable_cinder: yes
enable_cinder_backup: no

#cinder_backend_ceph: no

#enable_cinder_backend_lvm: no
#cinder_volume_group: cinder-volumes

# For Pure Storage/EMC and LVM, enable backend_iscsi
#enable_cinder_backend_iscsi: <yes or no>
```

## iscsid

```yaml
# set enable_iscsid to yes when enable_cider and enable_cinder_backend_iscsi equal yes
enable_iscsid: no
```

## Prometheus

```yaml
enable_prometheus: yes
# Prometheus cli flags
prometheus_cmdline_extras: "-storage.local.retention 360h -storage.local.target-heap-size 2147483648"
```
Values assigned to flags above are default values. Retention time can be changed
according to requirement. Default value of heap size is fine for 4 or 5 nodes cloud.
Increase it according to number of nodes sending data to prometheus-server. It's just an estimate.
In order to calculate it precisely, we need to know total number of timeseries.
For more information check https://prometheus.io/docs/prometheus/1.8/storage/#settings-for-high-numbers-of-time-series

For supported flags in prometheus v1.8, check [**this**](/prometheus-flags.html)

## Grafana

```yaml
enable_grafana: yes
```

## Horizon

Only enable Horizon if you won't be putting Arcus on ports 80 and 443 of the control nodes.

```yaml
enable_horizon: yes
```

## Gnocchi
Gnocchi depends on ceilometer for polling metrics. Enable both gnocchi and ceilometer.

```yaml
enable_ceilometer: yes
enable_gnocchi: yes
gnocchi_backend_storage: "ceph" or "file"
# Use following attribute if gnocchi_backend_storage is ceph pool name is other than "gnocchi"
ceph_gnocchi_pool_name:
```

## Central Logging

Central logging deploys elasticsearch and kibana. If enabling elasticsearch_curator, you can also
set soft and hard retention time. Indices are closed after soft retention period and deleted after
hard retention period.
```yaml
enable_central_logging: "yes"
enable_elasticsearch_curator: "yes"
elasticsearch_curator_soft_retention_period_days: 15
elasticsearch_curator_hard_retention_period_days: 15
```
Older checkouts of kolla-ansible stable/train weren't supporting elasticsearch curator.
If you are installing elasticsearch curator on an existing cloud, please ensure that
elasticsearch curator hosts are defined in inventory in next step.
