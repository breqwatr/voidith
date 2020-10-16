# Create custom archive policy
If arcus metering is enabled on this cloud then a custom archive policy is required.

## Source admin-rc file
```
source /etc/kolla/admin-openrc.sh
```

## Create archive policy
Use archive policy name used in step [**Write Kolla-Ansible's config/ files**](/openstack-kolla-config.html)
```
openstack metric archive-policy create metering-policy \
 -d "granularity:00:05:00","timespan: 2 hours" \
 -d "granularity:01:00:00","timespan: 33 days" -m mean
```

## Delete default archive policy rule
```
openstack metric archive-policy-rule delete default
```

## Create new default archive policy rule
```
openstack metric archive-policy-rule create -a metering-policy -m "*" default
```

## Restart ceilometer and gnocchi containers
```
docker restart gnocchi_api gnocchi_metricd gnocchi_statsd ceilometer_central ceilometer_compute ceilometer_notification

```
