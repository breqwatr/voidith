# OpenStack Server Setup

1. Verify hardware requirements
1. Install Ubuntu 18.04
1. Configure Networking
1. Install Python

## Recommended Hardware Requirements

While the installation will succeed with fewer resources than are listed here,
we wouldn't suggest using anything less outside of testing.

In small clusters, control and compute roles can be on the same nodes. In that
scenario, aim to have a bit higher than the compute node requirements.

**Control Node**:

- Two 200GB+ SSD operating system drives in RAID 1 (mirroring) configuration
- 16GB RAM
- 8 CPUs @ 2.67+ GHz
- Two 10 GB/s interfaces (4 if interface HA is required)


**Compute Node**:

- Two 200GB+ SSD operating system drives in RAID 1 (mirroring) configuration
- 32GB RAM - More is better. RAM is usually the bottleneck determining how many
  instances can be created on a host.
- 24 CPU's @ 2.67+ GHz (before hyperthreading)
- Two 10 GB/s interfaces (4 if interface HA is required)
- (optional) local drives to be used as non-shared VM block device storage.
  Cinder will consume these drives using the LVM plugin.


## Hardware Virtualization Support

When deploying on metal servers, it is assumed that hardware virtualization is 
supported by the chosen processors and enabled in the BIOS of each compute node.

It can save some trouble to verify this is enabled before installation.


## Networking Configuration

Ubuntu 18.04 uses [Netplan](https://netplan.io/examples) to configure interface
networking.

OpenStack Neutron requires a dedicated interface for "overcloud" traffic.
All infrastructure ("undercloud") traffic goes on a separate interface.

Two approaches will be shown here. The first is recomended for production or
significant POC deployments. The second is recomended for very small test
deployments.

### Recomended Network Setup

For security reasons, it's advantageous to segregate the undercloud networks
into 3 VLANs and subnets.

1. **Storage network:** This network isn't required if local LVM-driven storage
   will be used. If Ceph or an external storage appliance such as Pure Storage
   or EMC will be used, their traffic should be on this VLAN. The storage
   network should be a flat layer 2 subnet trunked between each OpenStack node,
   the deployment server, and the storage servers or appliances.
	 Often this network will also benefit from having its MTU value increased to
   9000.
1. **Internal infrastructure network:** OpenStack services use RabbitMQ for its
   message queues and MariaDB as a database. Both are deployed as highly
   available clusters. OpenStack services will also communicate over HTTP APIs
   between the nodes. These services and communications should exist on a
   dedicated internal VLAN and subnet. The internal network should only be
   trunked between the OpenStack nodes.
1. **Public API network:** This network hosts the OpenStack APIs. Any users
   who will be operating OpenStack from the command-line or the Horizon web
   interface will need Layer 3 routed access to the IP addresses on this
   network.

This is a Netplan example of a 4-port server's network configuration. In this
example, `bond0` is split into the three undercloud networks (VLANs 10, 11, and
12). The other bond, `bond1`, is left unused so Neutron can
consume it. For LACP or any other network configuration options reference the
[Netplan](https://netplan.io/examples) documentation.


**A note about MTUs**: Commonly you won't want the public and internal network to use a special MTU
value, since the gateway upstream is likely using MTU 1500. Unfortunately to allow guests to use
MTU 9000, such as those which want to run their own iSCSI services, you must configure the bonds
and ethernet adapters as MTU 9000. In the below example, bond0 is the network specified by
`neutron_external_interface` in Kolla-Ansible's `globals.yml` file. Note that the VLAN interfaces
are configured to still use 1500. It's best to do this *before* a user requests MTU 9000 on a VM,
as otherwise you'll have to do it live in production.

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eno1:
      dhcp4: no
      mtu: 9000
    eno2:
      dhcp4: no
      mtu: 9000
    enp179s0f0:
      dhcp4: no
    enp179s0f1:
      dhcp4: no
  bonds:
    bond0:
      parameters:
        mode: active-backup
        mii-monitor-interval: 100
      interfaces: [eno1, eno2]
      dhcp4: no
      mtu: 9000
      addresses: ["10.62.0.11/24"]
    bond1:
      parameters:
        mode: active-backup
        primary: enp179s0f1
      interfaces: [enp179s0f0, enp179s0f1]
  vlans:
    vlan10:
      id: 10
      accept-ra: no
      link: bond0
      mtu: 1500
      addresses: ["10.100.10.11/24"]
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
      gateway4: 10.100.10.1
    vlan11:
      id: 11
      accept-ra: no
      link: bond0
      mtu: 1500
      addresses: ["10.100.11.11/24"]
    vlan12:
      id: 12
      accept-ra: no
      link: bond0
      mtu: 1500
      addresses: ["10.100.12.11/24"]
```




## SSH Settings

### Authorize deployment server's key

Create an SSH directory for the root user

```bash
mkdir -p /root/.ssh
```

Then add the deployment server's public SSH key to
`/root/.ssh/authorized_keys`.


### Allow private-key SSH to root user

Ansible will be connecting to the root user via SSH using a private key
generated on the deployment server. The deployment server's public key will
be authorized on these hosts once generated.

Edit `/etc/ssh/sshd_config` and make sure the following value is set. This is
the default value so often no change is required.

```
# /etc/ssh/sshd_config
PermitRootLogin prohibit-password
```


## Installing Python

Ansible will expect Python to be installed on each OpenStack node.

```bash
# Install Python packages
apt-get -y install python python3 python-pip

# Install python docker library - this does not install Docker itself
pip install docker
```


## Configure /etc/hosts

On each OpenStack server, add hosts entries for each other OpenStack server.
If you're using an isolated private network, that's the one that should have
the host entries else RabbitMQ will fail on first reboot in the control nodes.

Similarly if Ceph is used, add entries for each Ceph node as well. Use the
client network IP if Ceph has its network segregated too.

DNS can be a solution to avoiding this, but generally the OpenStack internal
network is not the network with the default gateway, so `/etc/hosts` tends to
be a better option.


## Disable NTP on the hosts

Chrony will handle NTP for the OpenStack servers, so disable the NTP service in systemctl.

```bash
# If it's not found, skip this
systemctl disable ntp
```


## Set Swappiness

You don't want Linux using the swap disk before it really must.

Apply the change immediately by running: `echo 5 > /proc/sys/vm/swappiness`

Have the setting also apply at reboot: At the end of /etc/sysctl.conf set 

```
vm.swappiness=5
```

If you want to clear your swap currently used, and you're sure you won't hurt anything right now, you can run:
```
swapoff -a; swapon -a
```


