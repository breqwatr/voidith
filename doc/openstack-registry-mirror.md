[Index](/)
\> Mirroring OpenStack Release's Images on Local Registry

# Mirroring OpenStack Release's Images on Local Registry

Before attempting to sync the Docker Hub images to your local registry, ensure
that it's deployed.

- [Deploying the local registry service](/registry.html)

In a normal installation you'll want to sync all of the OpenStack images using
the `sync-openstack-images` command. Individual images can be later
synchronized for the purpose of updates.

```bash
# Load all OpenStack images to the local registry
voithos service registry sync-openstack-images \
  --release <openstack release> \
  <registry ip:port>

# sync-openstack-images example
voithos service registry sync-openstack-images -r stein 10.10.10.9:5000
```

If you need to sync a specific image, for instance to update one service,
the `sync-image` command is available:

```bash
# Load a specific image
voithos service registry sync-image --tag <tag> <registry ip:port> <repository name>

# sync-image example
voithos service registry sync-image --tag stein 10.10.10.9:5000 ubuntu-source-mariadb
```

