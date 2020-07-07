[Index](/)
\> [OpenStack Installation](/openstack-install.html)
\> Mirroring OpenStack Release's Images on Local Registry

# Mirroring OpenStack Release's Images on Local Registry

Before attempting to sync the Docker Hub images to your local registry, ensure
that it's deployed.

[Deploying the local registry service.](/registry.html)

In a normal installation you'll want to sync all of the OpenStack images using
the `sync-openstack-images` command. Individual images can be later
synchronized for the purpose of updates.

```bash
# Load all OpenStack images to the local registry
voithos openstack sync-images-to-registry --release <openstack release> <proto://registry ip:port>

# sync-openstack-images example
voithos openstack sync-images-to-registry -r train http://10.10.10.9:5000
```

If you need to sync a specific image, for instance to update one service,
the `sync-image` command is available:

```bash
# Load a specific image
vouthos service registry sync-image --tag <tag> <registry ip:port> <repository name>

# sync-image example
voithos service registry sync-image --tag train 10.10.10.9:5000 ubuntu-source-mariadb
```

