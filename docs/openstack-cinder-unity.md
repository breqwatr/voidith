# Cinder Unity Integration

## config/cinder.conf

[driver options](https://github.com/emc-openstack/unity-cinder-driver#driver-options)

```ini

[DEFAULT]
enabled_backends = unity

[unity]
storage_protocol = iSCSI
san_ip = 10.1.0.242
san_login = openstack
san_password = 7TpGA!4Jxu
volume_driver = cinder.volume.drivers.dell_emc.unity.Driver
volume_backend_name = Storage_ISCSI_01
unity_storage_pool_names = pool1
```
