# Grafana and Prometheus Configurations
Prometheus is a monitoring tool that scrapes monitoring data and Grafana use that data to 
create graphs.

## SMTP Configuration
SMTP configuration is needed to setup email alerts through Grafana. Put these configs in
`/etc/kolla/grafana/grafana.ini` and restart grafana container.
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

## TLS Configuration
If tls is enabled in your deployment then add `verify: false` under `default` in
`/etc/kolla/prometheus-openstack-exporter/clouds.yml` and restart prometheus-openstack-exporter
container

## Access Grafana Webui
Access grafana webui using <external-vip>:3000 or <internal-vip>:3000. Username is `admin` and
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
* Add the name of channel and comma separated email address.
* Click on `Send Test` and save if it sends a test email.

## Create Dashboard
* Hover over `Dashboards` symbol (2nd symbol) on the left hand side and click on `Manage`.
* Click on `New Dashboard` button.
* Now click on save button (2nd symbol on top right corner). Enter the name of dashboard and
click on `Save` button

## Create Panels
**For creating a new graph follow these steps**
* Click on `Add panel` button (1st button on top right). It will open a new panel.
* Click on `Add Query` button inside new panel.
* Click datasource dropdown next to `Query` and choose `Prometheus`.
* In the `Metric` field put the query for monitoring a resource.
* Check queries for different resources in section below.
* Click on `General` symbol (2nd symbol) on left side and add panel title.
* Click on back button on top left corner.
* Click save button (4th symbol) on top right corner and save it.

## Example Queries

### CPU Idle
* **Query:** (avg by (instance) (irate(node_cpu_seconds_total{job="node",mode="idle"}[5m])) * 100)

### Free Memory
* **Query:** node_memory_MemFree_bytes
* Click on `Visualization` symbol on left side.
* Under `Axes` section, in `Left Y` part, click on `Unit` dropdown list.
* Click on `Data (IEC)` and choose `bytes`.

### Available Memory
* **Query:** node_memory_MemAvailable_bytes
* Click on `Visualization` symbol on left side.
* Under `Axes` section, in `Left Y` part, click on `Unit` dropdown list.
* Click on `Data (IEC)` and choose `bytes`.

### Boot Disk Free
* **Query:** node_filesystem_avail_bytes{mountpoint="/"}

### Network Bytes Received 
* **Query:** irate((node_network_receive_bytes_total{device=~"en.*"}[5m]))
* Click on `Visualization` symbol on left side.
* Under `Axes` section, in `Left Y` part, click on `Unit` dropdown list.
* Click on `Data (IEC)` and choose `bytes`.
**Note**: In device part of query above, put the pattern of interface name
          For example, put "eno.*" for int names eno1, eno2 etc

### Network Bytes Transmitted
* **Query:** irate((node_network_transmit_bytes_total{device=~"en.*"}[5m]))
* Click on `Visualization` symbol on left side.
* Under `Axes` section, in `Left Y` part, click on `Unit` dropdown list.
* Click on `Data (IEC)` and choose `bytes`.
**Note**: In device part of query above, put the pattern of interface name
          For example, put "eno.*" for int names eno1, eno2 etc

### Node State
* **Query:** up{job="node"}

### Network Interface State
* **Query:** node_network_up{job="node", interface=~"eno.*"}
**Note**: In interface part of query above, put the pattern of interface name
          For example, put "eno.*" for int names eno1, eno2 etc


## Alerts Setup

### CPU Idle
* Hover over the name of graph for cpu idle.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name 
    * evaluation interval: `1m`
    * time: `5m`
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Add minimun percent of cpu idle to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message 

### Free Memory
* Hover over the name of graph for free memory.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Add minimun bytes of free memory to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message


### Boot Disk Free
* Hover over the name of graph for free boot disk.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Add minimun bytes of free disk to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message

### Network Bytes Received
* Hover over the name of graph for network bytes received.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `max()`
    * OF: `query (A, 5m, now)`
    * Keep `IS ABOVE`
    * Add maximum bytes received to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message

### Network Bytes Transmitted
* Hover over the name of graph for network bytes transmitted.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `max()`
    * OF: `query (A, 5m, now)`
    * Keep`IS ABOVE`
    * Add maximum bytes transmitted to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message

### Node State
* Hover over the name of graph for nodes state.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Put 1 to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message

### Network Interface State
* Hover over the name of graph for network interfaces state.
* Click on dropdown button and click on `edit`.
* Click on `Alert` symbol (last symbol) on left side and click on `Create Alert` button.
  * In `Rule` section add:
    * name
    * evaluation interval: `1m`
    * time: `5m` 
  * In `Conditions` section add:
    * When: `min()`
    * OF: `query (A, 5m, now)`
    * Click on `IS ABOVE` and choose `IS BELOW`
    * Add 1 to trigger alert.
  * In `Notifications` section:
    * Next to `Send to`, click on `+` symbol and choose your notification channel.
    * In message form enter the alert message
