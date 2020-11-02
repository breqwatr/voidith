# Prometheus cli flags in v1.8

```yaml
./prometheus -h
usage: prometheus [<args>]

  
   -version false
      Print version information.
  
   -config.file "prometheus.yml"
      Prometheus configuration file name.
  
 == ALERTMANAGER ==
  
   -alertmanager.notification-queue-capacity 10000
      The capacity of the queue for pending alert manager notifications.
  
   -alertmanager.timeout 10s
      Alert manager HTTP API timeout.
  
   -alertmanager.url 
      Comma-separated list of Alertmanager URLs to send notifications to.
  
 == LOG ==
  
   -log.format "\"logger:stderr\""
      Set the log target and format. Example: 
      "logger:syslog?appname=bob&local=7" or "logger:stdout?json=true"
  
   -log.level "\"info\""
      Only log messages with the given severity or above. Valid levels: 
      [debug, info, warn, error, fatal]
  
 == QUERY ==
  
   -query.max-concurrency 20
      Maximum number of queries executed concurrently.
  
   -query.staleness-delta 5m0s
      Staleness delta allowance during expression evaluations.
  
   -query.timeout 2m0s
      Maximum time a query may take before being aborted.
  
 == STORAGE ==
  
   -storage.local.checkpoint-dirty-series-limit 5000
      If approx. that many time series are in a state that would require 
      a recovery operation after a crash, a checkpoint is triggered, even if 
      the checkpoint interval hasn't passed yet. A recovery operation requires 
      a disk seek. The default limit intends to keep the recovery time below 
      1min even on spinning disks. With SSD, recovery is much faster, so you 
      might want to increase this value in that case to avoid overly frequent 
      checkpoints. Also note that a checkpoint is never triggered before at 
      least as much time has passed as the last checkpoint took.
  
   -storage.local.checkpoint-interval 5m0s
      The time to wait between checkpoints of in-memory metrics and 
      chunks not yet persisted to series files. Note that a checkpoint is never 
      triggered before at least as much time has passed as the last checkpoint 
      took.
  
   -storage.local.chunk-encoding-version 1
      Which chunk encoding version to use for newly created chunks. 
      Currently supported is 0 (delta encoding), 1 (double-delta encoding), and 
      2 (double-delta encoding with variable bit-width).
  
   -storage.local.dirty false
      If set, the local storage layer will perform crash recovery even if 
      the last shutdown appears to be clean.
  
   -storage.local.engine "persisted"
      Local storage engine. Supported values are: 'persisted' (full local 
      storage with on-disk persistence) and 'none' (no local storage).
  
   -storage.local.index-cache-size.fingerprint-to-metric 10485760
      The size in bytes for the fingerprint to metric index cache.
  
   -storage.local.index-cache-size.fingerprint-to-timerange 5242880
      The size in bytes for the metric time range index cache.
  
   -storage.local.index-cache-size.label-name-to-label-values 10485760
      The size in bytes for the label name to label values index cache.
  
   -storage.local.index-cache-size.label-pair-to-fingerprints 20971520
      The size in bytes for the label pair to fingerprints index cache.
  
   -storage.local.max-chunks-to-persist 0
      Deprecated. This flag has no effect anymore.
  
   -storage.local.memory-chunks 0
      Deprecated. If set, -storage.local.target-heap-size will be set to 
      this value times 3072.
  
   -storage.local.num-fingerprint-mutexes 4096
      The number of mutexes used for fingerprint locking.
  
   -storage.local.path "data"
      Base path for metrics storage.
  
   -storage.local.pedantic-checks false
      If set, a crash recovery will perform checks on each series file. 
      This might take a very long time.
  
   -storage.local.retention 360h0m0s
      How long to retain samples in the local storage.
  
   -storage.local.series-file-shrink-ratio 0.1
      A series file is only truncated (to delete samples that have 
      exceeded the retention period) if it shrinks by at least the provided 
      ratio. This saves I/O operations while causing only a limited storage 
      space overhead. If 0 or smaller, truncation will be performed even for a 
      single dropped chunk, while 1 or larger will effectively prevent any 
      truncation.
  
   -storage.local.series-sync-strategy "adaptive"
      When to sync series files after modification. Possible values: 
      'never', 'always', 'adaptive'. Sync'ing slows down storage performance 
      but reduces the risk of data loss in case of an OS crash. With the 
      'adaptive' strategy, series files are sync'd for as long as the storage 
      is not too much behind on chunk persistence.
  
   -storage.local.target-heap-size 2147483648
      The metrics storage attempts to limit its own memory usage such 
      that the total heap size approaches this value. Note that this is not a 
      hard limit. Actual heap size might be temporarily or permanently higher 
      for a variety of reasons. The default value is a relatively safe setting 
      to not use more than 3 GiB physical memory.
  
   -storage.remote.graphite-address 
      WARNING: THIS FLAG IS UNUSED! Built-in support for InfluxDB, 
      Graphite, and OpenTSDB has been removed. Use Prometheus's generic remote 
      write feature for building remote storage integrations. See 
      https://prometheus.io/docs/operating/configuration/#<remote_write>
  
   -storage.remote.graphite-prefix 
      WARNING: THIS FLAG IS UNUSED! Built-in support for InfluxDB, 
      Graphite, and OpenTSDB has been removed. Use Prometheus's generic remote 
      write feature for building remote storage integrations. See 
      https://prometheus.io/docs/operating/configuration/#<remote_write>
  
   -storage.remote.graphite-transport 
      WARNING: THIS FLAG IS UNUSED! Built-in support for InfluxDB, 
      Graphite, and OpenTSDB has been removed. Use Prometheus's generic remote 
      write feature for building remote storage integrations. See 
      https://prometheus.io/docs/operating/configuration/#<remote_write>
  
   -storage.remote.influxdb-url 
      WARNING: THIS FLAG IS UNUSED! Built-in support for InfluxDB, 
      Graphite, and OpenTSDB has been removed. Use Prometheus's generic remote 
      write feature for building remote storage integrations. See 
      https://prometheus.io/docs/operating/configuration/#<remote_write>
  
   -storage.remote.influxdb.database 
      WARNING: THIS FLAG IS UNUSED! Built-in support for InfluxDB, 
      Graphite, and OpenTSDB has been removed. Use Prometheus's generic remote 
      write feature for building remote storage integrations. See 
      https://prometheus.io/docs/operating/configuration/#<remote_write>
  
   -storage.remote.influxdb.retention-policy 
      WARNING: THIS FLAG IS UNUSED! Built-in support for InfluxDB, 
      Graphite, and OpenTSDB has been removed. Use Prometheus's generic remote 
      write feature for building remote storage integrations. See 
      https://prometheus.io/docs/operating/configuration/#<remote_write>
  
   -storage.remote.influxdb.username 
      WARNING: THIS FLAG IS UNUSED! Built-in support for InfluxDB, 
      Graphite, and OpenTSDB has been removed. Use Prometheus's generic remote 
      write feature for building remote storage integrations. See 
      https://prometheus.io/docs/operating/configuration/#<remote_write>
  
   -storage.remote.opentsdb-url 
      WARNING: THIS FLAG IS UNUSED! Built-in support for InfluxDB, 
      Graphite, and OpenTSDB has been removed. Use Prometheus's generic remote 
      write feature for building remote storage integrations. See 
      https://prometheus.io/docs/operating/configuration/#<remote_write>
  
   -storage.remote.timeout 
      WARNING: THIS FLAG IS UNUSED! Built-in support for InfluxDB, 
      Graphite, and OpenTSDB has been removed. Use Prometheus's generic remote 
      write feature for building remote storage integrations. See 
      https://prometheus.io/docs/operating/configuration/#<remote_write>
  
 == WEB ==
  
   -web.console.libraries "console_libraries"
      Path to the console library directory.
  
   -web.console.templates "consoles"
      Path to the console template directory, available at /consoles.
  
   -web.enable-remote-shutdown false
      Enable remote service shutdown.
  
   -web.external-url 
      The URL under which Prometheus is externally reachable (for 
      example, if Prometheus is served via a reverse proxy). Used for 
      generating relative and absolute links back to Prometheus itself. If the 
      URL has a path portion, it will be used to prefix all HTTP endpoints 
      served by Prometheus. If omitted, relevant URL components will be derived 
      automatically.
  
   -web.listen-address ":9090"
      Address to listen on for the web interface, API, and telemetry.
  
   -web.max-connections 512
      Maximum number of simultaneous connections.
  
   -web.read-timeout 30s
      Maximum duration before timing out read of the request, and closing 
      idle connections.
  
   -web.route-prefix 
      Prefix for the internal routes of web endpoints. Defaults to path 
      of -web.external-url.
  
   -web.telemetry-path "/metrics"
      Path under which to expose metrics.
  
   -web.user-assets 
      Path to static asset directory, available at /user
```
