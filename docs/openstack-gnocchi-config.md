# Create custom archive policy
If arcus metering is enabled on this cloud then a custom archive policy is required.

## Source admin-rc file
```
source /etc/kolla/admin-openrc.sh
```

## Create archive policy
Use archive policy names used in step [**Write Kolla-Ansible's config/ files**](/openstack-kolla-config.html)
```
openstack metric archive-policy create metering-policy-utilization \
  -d "granularity:00:05:00,timespan:2hours" -m mean
openstack metric archive-policy create metering-policy-usage \
-d "granularity:01:00:00,timespan:33days" -m mean
```

## Delete default archive policy rule
```
openstack metric archive-policy-rule delete default
```

## Create new archive policy rules
```
openstack metric archive-policy-rule create -a metering-policy-usage \
-m "{vcpus,memory,volume.size}" usage
openstack metric archive-policy-rule create -a metering-policy-utilization \
-m "{cpu,memory.usage}" utilization
```

## Restart ceilometer and gnocchi containers
```
docker restart gnocchi_api gnocchi_metricd gnocchi_statsd ceilometer_central ceilometer_compute ceilometer_notification

```
