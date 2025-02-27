# RabbitMQ Check

![RabbitMQ Dashboard][1]

## Overview

This check monitors [RabbitMQ][2] through the Datadog Agent. It allows you to:

* Track queue-based stats: queue size, consumer count, unacknowledged messages, redelivered messages, etc
* Track node-based stats: waiting processes, used sockets, used file descriptors, etc
* Monitor vhosts for aliveness and number of connections

And more.

## Setup

Follow the instructions below to install and configure this check for an Agent running on a host. For containerized environments, see the [Autodiscovery Integration Templates][3] for guidance on applying these instructions.

### Installation

The RabbitMQ check is included in the [Datadog Agent][4] package. No additional installation is needed on your server.

### Configuration

Edit the `rabbitmq.d/conf.yaml` file, in the `conf.d/` folder at the root of your [Agent's configuration directory][5] to start collecting your RabbitMQ [metrics](#metric-collection) and [logs](#log-collection). See the [sample rabbitmq.d/conf.yaml][6] for all available configuration options.

#### Prepare RabbitMQ

Enable the RabbitMQ management plugin. See [RabbitMQ's documentation][7] to enable it.

The Agent user then needs at least the `monitoring` tag and these required permissions:

| Permission | Command            |
|------------|--------------------|
| **conf**   | `^aliveness-test$` |
| **write**  | `^amq\.default$`   |
| **read**   | `.*`               |

Create an Agent user for your default vhost with the following commands:

```
rabbitmqctl add_user datadog <SECRET>
rabbitmqctl set_permissions  -p / datadog "^aliveness-test$" "^amq\.default$" ".*"
rabbitmqctl set_user_tags datadog monitoring
```

Here, `/` refers to the default host. Set this to your specified virtual host name. See the [RabbitMQ documentation][8] for more information.

#### Metric collection

* Add this configuration block to your `rabbitmq.d/conf.yaml` file to start gathering your [RabbitMQ metrics](#metrics):

```
init_config:

instances:
  - rabbitmq_api_url: http://localhost:15672/api/
  #  username: <username> # if your RabbitMQ API requires auth; default is guest
  #  password: <password> # default is guest
  #  tag_families: true           # default is false
  #  vhosts:
  #    - <YOUR_VHOST>             # don't set if you want all vhosts
```

If you don't set `vhosts`, the Agent sends the following for EVERY vhost:

1. `rabbitmq.aliveness` service check
2. `rabbitmq.connections` metric

If you do set `vhosts`, the Agent sends this check and metric only for the vhosts you list.

There are options for `queues` and `nodes` that work similarly. The Agent checks all queues and nodes by default, but you can provide lists or regexes to limit this. See the [rabbitmq.d/conf.yaml][6] for examples.

Configuration Options:

| Option                           | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                 |
|----------------------------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `rabbitmq_api_url`               | Yes      | Points to the API url of the [RabbitMQ Managment Plugin][9].                                                                                                                                                                                                                                                                                                                                                |
| `tls_verify`                     | No      |  Set to `false` to skip verification of tls cert chain when the `rabbitmq_api_url` uses https. The default is `true`.                                                                                                                                                                                                                                                                                                                                              |
| `username`                       | No       | User name, defaults to 'guest'                                                                                                                                                                                                                                                                                                                                                                              |
| `password`                       | No       | Password, defaults to 'guest'                                                                                                                                                                                                                                                                                                                                                                               |
| `tag_families`                   | No       | Tag queue "families" based off of regex matching, defaults to false                                                                                                                                                                                                                                                                                                                                         |
| `nodes` or `nodes_regexes`       | No       | Use these parameters to specify the nodes you want to collect metrics on (up to 100). If you have less than 100 nodes, you don't have to set this parameter. The metrics are collected for all nodes by default.                                                                                                                                                                                            |
| `queues` or `queues_regexes`     | No       | Use these parameters to specify the queues you want to collect metrics on (up to 200). If you have less than 200 queues, you don't have to set this parameter. The metrics are collected for all queues by default. If you have set up vhosts, set the queue names as `vhost_name/queue_name`. If you have `tag_families` enabled, the first captured group in the regex is used as the `queue_family` tag. |
| `exchanges` or `exchanges_regex` | No       | Use these parameters to specify the exchanges you want to collect metrics on (up to 50). If you have less than 50 exchanges, you don't have to set this parameter. The metrics are collected for all exchanges by default.                                                                                                                                                                                  |
| `vhosts`                         | No       | By default a list of all vhosts is fetched and each one is checked using the aliveness API. If you prefer only certain vhosts to be monitored, list the vhosts you care about.                                                                                                                                                                                                                              |

[Restart the Agent][10] to begin sending RabbitMQ metrics, events, and service checks to Datadog.

#### Log collection

**Available for Agent >6.0**

1. To modify the default log file location either set the `RABBITMQ_LOGS` environment variable or add the following to your RabbitMQ configuration file (`/etc/rabbitmq/rabbitmq.conf`):

    ```conf
      log.dir = /var/log/rabbit
      log.file = rabbit.log
    ```

2. Collecting logs is disabled by default in the Datadog Agent, enable it in your `datadog.yaml` file:

    ```yaml
      logs_enabled: true
    ```

3. Add this configuration block to your `rabbitmq.d/conf.yaml` file to start collecting your RabbitMQ logs:

    ```yaml
      logs:
          - type: file
            path: /var/log/rabbit/*.log
            source: rabbitmq
            service: myservice
            log_processing_rules:
              - type: multi_line
                name: logs_starts_with_equal_sign
                pattern: "="
    ```

4. [Restart the Agent][10].

### Validation

[Run the Agent's status subcommand][11] and look for `rabbitmq` under the Checks section.

## Data Collected
### Metrics

See [metadata.csv][12] for a list of metrics provided by this integration.

The Agent tags `rabbitmq.queue.*` metrics by queue name and `rabbitmq.node.*` metrics by node name.

### Events

For performance reasons, the RabbitMQ check limits the number of exchanges, queues, and nodes it collects metrics for. If the check nears this limit, it emits a warning-level event to your event stream.

If you require an increase in the number of exchanges, queues, or nodes, contact [Datadog support][13].

### Service Checks

**rabbitmq.aliveness**:<br>
The Agent submits this service check for all vhosts (if `vhosts` is not configured) OR a subset of vhosts (those configured in `vhosts`). Each service check is tagged with `vhost:<vhost_name>`. Returns `CRITICAL` if the aliveness check failed, otherwise returns `OK`.

**rabbitmq.status**:<br>
Returns `CRITICAL` if the Agent cannot connect to RabbitMQ to collect metrics, otherwise returns `OK`.

## Troubleshooting

Need help? Contact [Datadog support][13].

## Further Reading
Additional helpful documentation, links, and articles:

### Datadog Blog
* [Key metrics for RabbitMQ monitoring][14]
* [Collecting metrics with RabbitMQ monitoring tools][15]
* [Monitoring RabbitMQ performance with Datadog][16]

### FAQ
* [Tagging RabbitMQ queues by tag family][17]


[1]: https://raw.githubusercontent.com/DataDog/integrations-core/master/rabbitmq/images/rabbitmq_dashboard.png
[2]: https://www.rabbitmq.com
[3]: https://docs.datadoghq.com/agent/autodiscovery/integrations
[4]: https://app.datadoghq.com/account/settings#agent
[5]: https://docs.datadoghq.com/agent/guide/agent-configuration-files/?tab=agentv6#agent-configuration-directory
[6]: https://github.com/DataDog/integrations-core/blob/master/rabbitmq/datadog_checks/rabbitmq/data/conf.yaml.example
[7]: https://www.rabbitmq.com/management.html
[8]: https://www.rabbitmq.com/rabbitmqctl.8.html#set_permissions
[9]: https://www.rabbitmq.com/management.html
[10]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6#start-stop-and-restart-the-agent
[11]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6#agent-status-and-information
[12]: https://github.com/DataDog/integrations-core/blob/master/rabbitmq/metadata.csv
[13]: https://docs.datadoghq.com/help
[14]: https://www.datadoghq.com/blog/rabbitmq-monitoring
[15]: https://www.datadoghq.com/blog/rabbitmq-monitoring-tools
[16]: https://www.datadoghq.com/blog/monitoring-rabbitmq-performance-with-datadog
[17]: https://docs.datadoghq.com/integrations/faq/tagging-rabbitmq-queues-by-tag-family
