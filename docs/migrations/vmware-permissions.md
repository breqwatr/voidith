[> Back to migration procedure](/vmware-migration.html)


# Voithos Migrations: Required VMware permissions

## Define Service Account

A service account is needed for Voithos to authenticate with each VCenter/VSphere environment.
Create a user and save the username, password, and VMware's IP address. They'll be used in
environment variables like so:


## Creating the vSphere Role

Create a new role from the Administration > Access Control > Roles sections of vSphere.

Clone the Read-Only role and name it something like `voithos` or `breqwatr-migrations`.

Under Global Permissions, assign the role to the above service account.


