[> Back to migration procedure](/vmware-migration.html)


# Voithos Migrations: Required VMware permissions

## Define Service Account

A service account is needed for Voithos to authenticate with each VCenter/VSphere environment.
Create a user and save the username, password, and VMware's IP address. They'll be used in
environment variables like so:


## Create the Role

For the most part, only read access is required. Duplicate the Read-Only role and make a new one,
and give it a useful name -for example `voithos` or `breqwatr`. Navigate to the vApp section
and enable Export.

## Granting Access

From Hosts and Clusters, select the datacenter then go to Permissions. Add the service account,
and assign it the new role. The easiest configuration here is to select
`Propogate to Children`.

If granting access to the entire datacenter is not appropriate, ensure that all hosts,
datastores, virtual networksm distributed switches, etc grant access to the service account.
