[Index](/)
\> Generating Unique OpenStack Service Passwords

# Generating Unique OpenStack Service Passwords

OpenStack is a collection of many tightly knit products. To ensure the security
of the OpenStack cluster, each service must use its own, unique password. These
passwords should be unique not only to the service, but also between clouds.

The generated passwords are used, at minimum, to grant access to clustered
MariaDB databases and RabbitMQ message queues.

The [Kolla-Ansible](https://github.com/openstack/kolla-ansible) project
provides an Ansible playbook to automatically generate these passwords into
a YAML file.

Breqwatr has containerized the Kolla-Ansible service and
[freely distributes the image on Docker Hub](https://hub.docker.com/r/breqwatr/kolla-ansible).
This Kolla-Ansible image can be Orchestrated using the BWDT CLI to easily
generate a `passwords.yml` in the present working directory.

```bash
# creates ./passwords.yml
voidith openstack get-passwords --release <release name>
```

