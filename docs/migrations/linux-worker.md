[Back to the migration guide](/vmware-migration.html)


# Creating a Linux wigration worker

The Linux migration worker downloads VMDK files and maps them to Cinder volumes. It can also
`chroot` into Linux partitions to install and configure the migration target machine.

Requirements:
- Must exist inside the same OpenStack project where the migration target VM will be created
- Outbound internet connection

Breqwatr supports using an Ubuntu 18.04 VM, but others might work too.

Configuration steps:

```bash
# Install Docker and Python3
apt-get update
apt-get install docker.io python3 python3-pip virtualenv

# In your home directory, create a virtualenv
virtualenv --python=python3 env/
source env/bin/activate

# add the virtualenv to your bashrc for ease of use
cd
echo "source env/bin/activate" >> .bashrc

# install Voithos
pip install git+https://github.com/breqwatr/voithos.git

# install the OpenStack client
pip install python-openstackclient
```

## Create OpenRC file

The OpenStack client doesn't need to run on the migration worker, and network constraints often
preclude the posibility. When possible, things are easier if you can run `openstack` commands on
the worker.

Create a file named `<project>-openrc.sh`, and fill it in. Replace anything in `<point brackets>`:

```
for key in $( set | awk '{FS="="}  /^OS_/ {print $1}' ); do unset $key ; done
export OS_PROJECT_DOMAIN_NAME=Default
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_NAME=<project name>
export OS_TENANT_NAME=<project name>
export OS_USERNAME=<user name>
export OS_PASSWORD=<password>
export OS_AUTH_URL=https://<public vip/fqdn>:5000/v3
export OS_INTERFACE=public
export OS_ENDPOINT_TYPE=internalURL
export OS_IDENTITY_API_VERSION=3
export OS_REGION_NAME=RegionOne
export OS_AUTH_PLUGIN=password
```

Source the openrc file:

```bash
source <project>-openrc.sh
```

Consider adding that source command to the end of your `~/.bashrc` file, too.

