# Offline deployment server setup
This doc provides procedure for setting up deployment server for offline install.
In offline install, deployment server and cloud nodes don't have internet connectivity.
So, we need to download everything required for breqwatr cloud deployemnt.
First login to a ubuntu 18 server that has internet connectivity and attach a usb to it.

---
## Voithos Installation 

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

## Download Offline Media
Run this command to download offline media on your usb stick
```bash
voithos util export-offline-media --path <path-to-usb> --ceph-release <ceph-ansible-version> --bw-tag <bw-tag> --kolla-tag <kolla-tag>
```
If you want to download an individual container image, use this command:
```bash
voithos util export-offline-image --help
```

This command will download all packages and images required to deploy breqwatr cloud.
Now transfer this data on your ubuntu 18.04 deployment server.

## Install offline packages and voithos on deployment server
Set time zone to UTC
```bash
# After running the command mentioned below, select `None of the above` in area and `UTC` in time zone
sudo dpkg-reconfigure tzdata
```

Untar apt.tar.gz and voithos.tar.gz

```bash
tar -zxvf  /path/to/offline/media/apt.tar.gz
tar -zxvf  /path/to/offline/media/voithos.tar.gz 
```

Now setup apt sources
```bash
mv /etc/apt/sources.list /etc/apt/old_sources_list
vi /etc/apt/sources.list

# Add this in new sources.list file
deb [trusted=yes arch=amd64] file:/<untar-apt.tar.gz-path>/apt_packages/ ./

# Update source
apt-get update
```

## Install deployment server packages
```bash
 apt-get install -y python3 python3-pip virtualenv python3-openstackclient python3-gnocchiclient docker
```

## Create and source virtualenv
```bash
virtualenv --python=python3 env/
source env/bin/activate
```

## Install Voithos
```bash
cd /<untar-voithos.tar.gz-path/voithos_packages>
pip install -r requirements.txt --no-index --find-links dependencies/ voithos-1.0.tar.gz
```

## Start insecure registry from offline image
First trust the registry by updating `/etc/docker/daemon.json` with these configs:
```bash
{
   "insecure-registries" : ["<registry ip>:<port>"]
}
```
Then restart docker service.

Now start the registry using this command:
```bash
voithos service registry start --ip <ip> --port <port> --path /<path to offline_media>/images/breqwatr-registry-stable.docker
```

## Sync container images to registry
```bash
voithos service registry sync-offline-images-to-registry --path /<path to offline_media>/images/ --ceph-release <ceph-ansible-release> --bw-tag <tag> --kolla-tag <openstack-tag> <registry-ip:port>
```
If you want to sync an individual image to registry, use this command:
```bash
voithos service registry sync-offline-image-to-registry --help
```

## Start apt service container
```bash
voithos service apt start --ip <deployment-server-ip> --port <other than 80> --tag <kolla-tag>
```

Now go to all cloud servers and update their apt sources list file.
```bash
mv /etc/apt/sources.list /etc/apt/old_sources
vi /etc/apt/sources.list
# Put these configs in source.list
deb [trusted=yes arch=amd64] http://<deployment server ip>:<apt-container-port> <ubuntu-release> main
deb [trusted=yes arch=amd64] http://<deployment server ip>:<apt-container-port> <ubuntu-release>-updates main
deb [trusted=yes arch=amd64] http://<deployment server ip>:<apt-container-port> <ubuntu-release>-security main
```
Update sources
```bash
apt-get update
```

## Start pip service container
```bash
voithos service pip start --tag <kolla-tag>
```

Now go to all cloud servers and update/create pip.conf
```bash
vi /etc/pip.conf
# Add these configs in pip.conf
[global]
trusted-host = <Deployment server IP>
index-url = http://<Deployment server IP>:3141/root/pypi/+simple/

[search]
index = http://<Deployment server IP>:3141/root/pypi/
```

Now proceed with the next steps for cloud deployment.
