

voi·thos (voï-thós) n. One who or that which assists; a
subordinate or helper. — adj. 1. Holding a subordinate or
auxiliary place, office or rank. 2. Affording aid; assisting.
From the Greek βοηθός (voïthós)

### Private Cloud Helper

Voithos is a command-line toolkit used to deploy and manage the various services and utilities that
make up private clouds. Voithos was formerly known as the Breqwatr Deployment Tool.

This free and open source project is created and managed by Breqwatr.



## Installing Voithos

Voithos has been tested on Mac OSX Catalina, Ubuntu 18.04 Bionic, and Windows 10.

To install Voithos, check out the Git project and use pip in a virtualenv.

### Ubuntu 18.04 Installation

```bash
# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
apt-get update
apt-get install -y docker-ce

# Install python3
apt-get update
apt-get install -y python3 python3-pip virtualenv

# Clone the repository from GitHub
git clone https://github.com/breqwatr/voithos.git
cd voithos

# Create and source the virtualenv
virtualenv --python=python3 env/
source env/bin/activate

# Install voithos
pip install .
```
---


# Install Guides

- [**Installing Ceph**](/ceph-install.html):
  An open-source cloud storage solution
- [**Installing OpenStack**](/openstack-install.html):
  Private clouds providing virtualisation, SDN, and more
- [**Installing Arcus**](/arcus-install.html): Breqwatr's OpenStack self-service web portal
- [**Configure Grafana And Prometheus](/grafana-prometheus-config.html): Monitoring solution
