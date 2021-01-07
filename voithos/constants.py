""" Global voithos constants """

import os

# Packages required by deployment server.
OFFLINE_DEPLOYMENT_SERVER_PACKAGES = [
    "python3",
    "python3-pip",
    "python3-openstackclient",
    "docker",
    "virtualenv"
]

# Major release of this CLI, for use with "voithos version"
VOITHOS_VERSION = "1.00"

# Enabling dev mode toggles some features for developers such as mounting arcus code to docker
DEV_MODE = "VOITHOS_DEV" in os.environ and os.environ["VOITHOS_DEV"].lower() == "true"

# Images to pull when syncing the registry, organized by release
KOLLA_IMAGE_REPOS = {
    "rocky": [
        "ubuntu-source-neutron-server",
        "ubuntu-source-neutron-openvswitch-agent",
        "ubuntu-source-neutron-dhcp-agent",
        "ubuntu-source-neutron-l3-agent",
        "ubuntu-source-neutron-metadata-agent",
        "ubuntu-source-heat-api",
        "ubuntu-source-heat-engine",
        "ubuntu-source-heat-api-cfn",
        "ubuntu-source-nova-compute",
        "ubuntu-source-nova-novncproxy",
        "ubuntu-source-nova-ssh",
        "ubuntu-source-nova-placement-api",
        "ubuntu-source-nova-api",
        "ubuntu-source-nova-consoleauth",
        "ubuntu-source-nova-conductor",
        "ubuntu-source-keystone-ssh",
        "ubuntu-source-nova-scheduler",
        "ubuntu-source-keystone",
        "ubuntu-source-keystone-fernet",
        "ubuntu-source-cinder-volume",
        "ubuntu-source-cinder-api",
        "ubuntu-source-cinder-scheduler",
        "ubuntu-source-glance-api",
        "ubuntu-source-openvswitch-db-server",
        "ubuntu-source-openvswitch-vswitchd",
        "ubuntu-source-kolla-toolbox",
        "ubuntu-source-fluentd",
        "ubuntu-source-memcached",
        "ubuntu-source-multipathd",
        "ubuntu-source-nova-libvirt",
        "ubuntu-source-keepalived",
        "ubuntu-source-chrony",
        "ubuntu-source-mariadb",
        "ubuntu-source-haproxy",
        "ubuntu-source-iscsid",
        "ubuntu-source-rabbitmq",
        "ubuntu-source-cron",
        "ubuntu-source-tgtd",
        "ubuntu-source-horizon",
    ]
}

# STEIN RELEASE
KOLLA_IMAGE_REPOS["stein"] = KOLLA_IMAGE_REPOS["rocky"]
# nova-placement API was removed and replaced with just regular "placement-api"
KOLLA_IMAGE_REPOS["stein"].remove("ubuntu-source-nova-placement-api")
KOLLA_IMAGE_REPOS["stein"].append("ubuntu-source-placement-api")
# support for Magnum k8s-aas introduced. It uses octavia for k8s lb ingress
KOLLA_IMAGE_REPOS["stein"].extend(
    [
        "ubuntu-source-magnum-api",
        "ubuntu-source-magnum-conductor",
        "ubuntu-source-octavia-api",
        "ubuntu-source-octavia-base",
        "ubuntu-source-octavia-health-manager",
        "ubuntu-source-octavia-housekeeping",
        "ubuntu-source-octavia-worker",
    ]
)

# TRAIN RELEASE
KOLLA_IMAGE_REPOS["train"] = KOLLA_IMAGE_REPOS["stein"]
# nova-consoleauth was deprecated a few releases ago, removed in train
KOLLA_IMAGE_REPOS["stein"].remove("ubuntu-source-nova-consoleauth")
# Log and metric aggregation via prometheus and elasticsearch now supported
KOLLA_IMAGE_REPOS["train"].extend(
    [
        "ubuntu-source-elasticsearch",
        "ubuntu-source-prometheus-elasticsearch-exporter",
        "ubuntu-source-prometheus-alertmanager",
        "ubuntu-source-prometheus-blackbox-exporter",
        "ubuntu-source-prometheus-cadvisor",
        "ubuntu-source-prometheus-haproxy-exporter",
        "ubuntu-source-prometheus-memcached-exporter",
        "ubuntu-source-prometheus-mtail",
        "ubuntu-source-prometheus-mysqld-exporter",
        "ubuntu-source-prometheus-node-exporter",
        "ubuntu-source-prometheus-openstack-exporter",
        "ubuntu-source-prometheus-server",
        "ubuntu-source-kibana",
        "ubuntu-source-gnocchi-api",
        "ubuntu-source-gnocchi-metricd",
        "ubuntu-source-gnocchi-statsd",
        "ubuntu-source-ceilometer-compute",
        "ubuntu-source-ceilometer-ipmi",
        "ubuntu-source-ceilometer-notification",
        "ubuntu-source-ceilometer-central",
        "ubuntu-source-grafana"
    ]
)
