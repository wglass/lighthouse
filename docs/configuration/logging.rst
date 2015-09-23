Configuring Logging
===================

The content of the logging config file is passed along to the standard `logging`
lib's `dictConfig`_ method.  Lighthouse does not verify the configuration itself,
but the contents should conform to the `dict config schema` since that's what
the `logging` system expects.

Lighthouse *does* however provide two helper classes for logging: the
`CLIHandler`_ and the `ContextFilter`_.

As an example, this file sends logs to stdout with the `CLIHandler` attached, as
well as to the local syslog system with added "program" context via the
`ContextFilter`:

`logging.yaml`

.. code-block:: yaml

    version: 1
    disable_existing_loggers: False
    filters:
      context:
        "()": lighthouse.log.ContextFilter
    formatters:
      syslog:
        format: 'lighthouse: [%(program)s] [%(threadName)s] %(message)s'
    handlers:
      cli:
        class: 'lighthouse.log.cli.CLIHandler'
        stream: "ext://sys.stdout"
      syslog:
        class: 'logging.handlers.SysLogHandler'
        address: '/dev/log'
        facility: "local6"
        filters: ["context"]
        formatter: 'syslog'
    root:
      handlers: ['syslog', 'cli']
      level: "DEBUG"
      propagate: true


ContextFilter
~~~~~~~~~~~~~

A simple `logging.Filter` subclass that adds a "program" attribute to any
`LogRecord`s that pass through it.  For the `lighthouse-writer` script the
attribute is set to "WRITER", for `lighthouse-reporter` it is set to "REPORTER".

Useful for differentiating log lines between the two scripts.


CLIHandler
~~~~~~~~~~

Handy `logging.StreamHandler` subclass that colors the log lines based on the
thread the log originated from and the level (e.g. "info", "warning", debug",
etc.)

Some example lines::

    [2015-09-22 18:52:40 I][MainThread] Adding loggingconfig: 'logging'
    [2015-09-22 18:52:40 D][MainThread] File created: /Users/william/local-config/balancers/haproxy.yml
    [2015-09-22 18:52:40 I][MainThread] Adding balancer: 'haproxy'
    [2015-09-22 18:52:40 I][Thread-3] Updating HAProxy config file.
    [2015-09-22 18:52:40 D][MainThread] File created: /Users/william/local-config/discovery/zookeeper.yaml
    [2015-09-22 18:52:40 D][Thread-3] Got HAProxy version: (1, 5, 10)
    [2015-09-22 18:52:41 I][MainThread] Adding discovery: 'zookeeper'
    [2015-09-22 18:52:41 D][Thread-3] Got HAProxy version: (1, 5, 10)
    [2015-09-22 18:52:41 I][Thread-12] Connecting to zookeeper02.oregon.internal:2181
    [2015-09-22 18:52:41 I][Thread-7] Updating HAProxy config file.
    [2015-09-22 18:52:41 D][MainThread] File created: /Users/william/local-config/clusters/haproxy-web.yaml
    [2015-09-22 18:52:41 I][Thread-3] Gracefully restarted HAProxy.
    [2015-09-22 18:52:41 I][MainThread] Adding cluster: 'haproxy-web'


.. _dictConfig: https://docs.python.org/2/library/logging.config.html#logging.config.dictConfig
.. _`dict config schema`: https://docs.python.org/2/library/logging.config.html#logging-config-dictschema
