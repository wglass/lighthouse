Writing Load Balancer Plugins
=============================

The base class for balancer plugins (:class:`lighthouse.balancer.Balancer`)
is deceptively simple, most of the heavy lifting is left to plugin writers.

The only balancer-specific method a subclass must define is the `sync_file()`
method, however there are implicit requirements for a load balancer plugin
to work well, such as gracefully reacting to configuration changes without
dropping traffic and not placing limits to the number of potential nodes
handled.

Balancer plugins aren't necessary limited to *load* balancing either.  Any
sort of clustering system, such as the ones for RabbitMQ_ or PostgreSQL_
replication setups can benefit from having a balancer plugin that
automatically determines potential member nodes.  The only limit is your
imagination!


Examples
~~~~~~~~

The project includes an HAProxy balancer plugin via the
:class:`lighthouse.haproxy.balancer.HAProxy` class.  HAProxy is a powerful
tool with quite a bit of configurability so the support code to get the
plugin to work is extensive.


Required Methods
~~~~~~~~~~~~~~~~

* `validate_dependencies(cls)` *(classmethod)*:

  This classmethod should check that all required external dependencies for
  your plugin are met.

  If the requirements are met, this method should return `True`.  If not met
  it should return `False`.

* `validate_config(cls, config)` *(classmethod)*:

  The "config" argument to this classmethod is the result of loading the YAML
  config file for the plugin (e.g. `checks/mycheck.yaml` for the example above).

  This method should analyze the config dictionary object and raise a
  `ValueError` exception for any invalid content.


* `apply_config(self, config)`:

  This instance method's config argument is also the result of a loaded YAML
  config file, albeit one that has already been validated.

  This method should take the validated dictionary object and set any sort of
  attributes/state/etc. on the instance as necessary.

  .. warning::

     It it is *incredibly important* that this method be idempodent with regards
     to instances of your Balancer subclass.  Configurations can be altered at
     any time in any manner, sometimes with invalid values!  You want your
     plugin's state to refect the contents of the YAML config file at all times.

* `sync_file(self, clusters)`:

  This method takes a list of :class:`lighthouse.cluster.Cluster` instances
  and should write or update the load balancer's configuration files to reflect
  the member nodes of the clusters.


.. _RabbitMQ: https://www.rabbitmq.com
.. _PostgreSQL: http://www.postgresql.org
