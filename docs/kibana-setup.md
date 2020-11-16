# Kibana Setup

## Access dashboard
Access kibana dashboard using `<external-vip>:5601` or `<internal-vip>:5601`, whichever is applicable.
It will ask for username and password. Default user is `kibana`. You can get `kibana` user's password
in passwords.yml by running `cat /etc/kolla/passwords.yml | grep kibana_password`

## Initial setup
After logging in, it will take you to `Management` tab for setting up index pattern.
Put `flog-*` in index pattern, choose `@timestamp` for `Time filter field name`
and click on create.

Then you can go to `Discover` tab and filter logs.
