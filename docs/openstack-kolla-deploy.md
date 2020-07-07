# Initialize OpenStack Containers with Kolla-Ansible Deploy

Before executing `deploy`, confirm everything is ready:

- The [globals file](/openstack-kolla-globals.html) has been written
- The [passwords](/openstack-kolla-passwords.html) are generated
- The [inventory](/openstack-kolla-inventory.html) is written
- The [certificates directory](/openstack-kolla-certificates.html) exists and contains the correct
  certificates - self-signed or otherwise
- The [config directory](/openstack-kolla-config.html) contains any service files or overrides

Use the following command to deploy OpenStack:

```bash
# Note: --config-dir is optional and can be ommitted

voithos openstack kolla-ansible deploy \
  --release train \
  --ssh-key ~/.ssh/id_rsa \
  --globals globals.yml \
  --passwords passwords.yml \
  --inventory inventory \
  --certificates certificates/ \
  --config config/
```
