[Index](/)
\> Local Docker Registry

# Local Docker Registry

The local Docker registry is required for offline/air-gap installations.

While optional for internet-enabled installations,  multi-node clusters benefit
from using a local registry. The registry service acts as a local cache to
prevent downloading tens of gigabytes of image data repeatedly on each cloud
server.


## Requirements

The Registry service is a Docker image, so it can technically run anywhere
Docker is installed. Since Registry is deployed using BWDT, Ubuntu 18.04 is
suggested.


## Deploying Registry

```bash
# Show the available options for starting the registry service
voidith service registry start --help

# Launch the registry on port 5000, listening on all IPs
voidith service registry start --ip 0.0.0.0 --port 5000
```

## Configure Docker to trust the local registry

Before you can sync images to the registry service or pull images from it,
you need to configure the Docker service to trust this registry.

On the deployment server, edit `/etc/docker/daemon.json` with content similar
to the following. Change the IP address and port as appropriate.

```
{
   "insecure-registries" : ["10.10.10.9:5000"]
}
```

Restart the docker service to apply the changes.

```bash
systemctl restart docker
```

At this point you may want to
[mirror the upstream OpenStack images](openstack-registry-mirror.html).


---


## List images in local registry

To list the images currently stored in the local registry:

```bash
voidith service registry list-images <registry ip:port>

# example
voidith service registry list-images 10.10.10.9:5000
```
