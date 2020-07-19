# Grafana and Prometheus Configurations

## SMTP Configuration
SMTP configuration is needed to setup email alerts through Grafana. Put these configs in
`/etc/kolla/grafana/grafana.ini` on all the servers on which grafana containers are running
and restart those containers using `docker restart grafana`.
```yaml
[smtp]                                                           
enabled =true                   
host = <host:port>
user = <user>
# If the password contains # or ; you have to wrap it with triple quotes. Ex """#password;"""
password = <password>                 
cert_file =                                        
key_file =
skip_verify = false                                                                                                     
from_address = <email address for sending alerts>
from_name = Grafana
# EHLO identity in SMTP dialog (defaults to instance_name)
ehlo_identity =  
```

## Grafana Domain Configuration
Kolla-ansible doesn't configure domain address by default. So when we get an alert through email,
it has a tab that should redirect to grafana alert webui address. If the domain isn't configured,
it will redirect to `localhost:3000` instead of `grafana-webui-ip:3000`. In order to configure that
open `/etc/kolla/grafana/grafana.ini` and put `domain = <api_interface_address>` under `[server]`.
`<api_interface_address>` will be same as `http_addr` configured under `[server]`. Do this on all
the servers on which grafana containers are running and restart containers using
`docker restart grafana`.


## TLS Configuration
If tls is enabled in your deployment then add `verify: false` under `default` in
`/etc/kolla/prometheus-openstack-exporter/clouds.yml` and restart prometheus_openstack_exporter
container using `docker restart prometheus_openstack_exporter`

## Access Grafana Webui
Access grafana webui using `<external-vip>:3000` or `<internal-vip>:3000`. Username is `admin` and
it's password can be found by running `cat /etc/kolla/grafana/grafana.ini | grep admin_password`

## Invite Users
* Hover over `Configuration` symbol (2nd last symbol) on the left hand side and click on `Users`.
* On the right side, click on `Invite` button.
* Fill the forms and click on submit.
**Note**: It will fail if smtp isn't configured.

## Create Notification Channel
**Note:** Skip this section if you don't want to setup alerts.
For setting up email alert, first we have to create a notification channel
* Hover over `Alerting` symbol (4th symbol) on the left hand side and click on 
`Notification channels`.
* Click on `Add Channel` button.
* Add the name of channel.
* Enable `Default` if you want to add this channel to all alerts.
* Add comma separated email addresses.
* Click on `Send Test` and save if it sends a test email.

**Note**: If you will be creating graphs and alerts using a voithos script, create a
default notification channel to which all the script created alerts will be sent. 
