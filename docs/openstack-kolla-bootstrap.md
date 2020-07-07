# Kolla-Ansible's Bootstrap Playbook

Once the servers that will host OpenStack services are online, have their
networks configured, and the deployment server can SSH to them using its
SSH private key, the server is ready for the bootstrap playbook.

This step will install Docker and some other packages. When using local/offline
mirrors for apt and pip then Kolla-Ansible's globals file needs to be
pointed at them.

The servers that will host OpenStack services should now be online and have
their networks and SSH `authorized_keys` files configured, but they need
Docker and some other packages to be fully ready to launch the OpenStack
containers. The bootstrap step will finalize their preparation.

Use the following syntax to run Kolla-Ansible's bootstrap through the
Kolla-Ansible Docker image, orchestrated by Voithos:

```bash
voithos openstack kolla-ansible bootstrap-servers \
  --release train \
  --ssh-key ~/.ssh/id_rsa \
  --globals globals.yml \
  --passwords passwords.yml \
  --inventory inventory \
  --certificates certificates
```
