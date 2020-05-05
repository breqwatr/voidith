# Voidith
## A private cloud helper by Breqwatr

Voidith is a command-line toolkit used to deploy and manage the various services and
utilities that make up private clouds.

While this project is created and Managed by Breqwatr, it's open source and free for
anyone to use.

Voidith was formerly known as the Breqwatr Deployment Tool.


## Installation & Requirements

Voidith is built upon Docker and Python, so in theory it should be able to run anywhere
they do. In practice, it is tested against Mac OSX and Ubuntu Server 18.04.

To install Voidith, check out the git project and use pip in a virtualenv.

On Ubuntu:

```bash
# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
apt-get update
apt-get install -y docker-ce

# Install python3
apt-get update
apt-get install -y python3 python3-pip virtualenv

# Clone the repo
git clone https://github.com/breqwatr/voidith.git
cd voidith

# Create and source the virtualenv
virtualenv --python=python3 env/
source env/bin/activate

# Install voidith
pip install .
```
---


# Cluster Install Guides

- [**Installing Ceph**](/ceph-install.html):
  An open-source cloud storage solution
