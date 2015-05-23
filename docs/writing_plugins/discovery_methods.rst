Writing Discovery Method Plugins
================================

Discovery plugins handle storing the topography data of clusters and services,
the required functionality boils down to two things: "watching" and "reporting".

A plugin must be able to "watch" for changes in membership for clusters and
react accordingly, updating Cluster instances and setting `should_update`
events when they occur.  Likewise, the plugin must *also* be able to cause such
changes in membership by reporting nodes as available or down.

These plugins must be subclasses of :class:`lighthouse.discovery.Discovery`,
for an example implementation for using Zookeeper_ see the
:class:`lighthouse.zookeeper.ZookeeperDiscovery` class.

Having nodes agree with each other on the makeup of clusters they consume
and/or take part in is important.  The best candidates for discovery methods
are strong `"CP" distributed systems`_, that is reliable systems that give
solid guarantees that nodes interacting with it see the same thing regardless
of where they are.


Required Methods
~~~~~~~~~~~~~~~~

* `validate_dependencies(cls)` *(classmethod)*:

  This classmethod should check that all required external dependencies for
  your plugin are met.

  If the requirements are met, this method should return True.  If not met
  it should return False.

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

     It it is *incredibly important* that this method be idempotent with regards
     to instances of your Discovery subclass.  Configurations can be altered at
     any time in any manner, sometimes with invalid values!  You want your
     plugin's state to reflect the contents of the YAML config file at all times.


* `connect()`:

  This method should handle any sort of connection establishment to the discovery
  method system.  It takes no arguments.

* `disconnect()`:

  The `disconnect()` method is called when shutting down the discovery method
  and should take care of undoing any actions taken by the `connect()` call.

* `start_watching(self, cluster, should_update)`:

  This method registers a cluster to be "watched" by the discovery method.
  Whenever an update to the set of member nodes happens, this method must
  update the `nodes` list of the passed-in :class:`lighthouse.cluster.Cluster`
  instance and call `set()` on the `should_update` threading event.

* `stop_watching(self, cluster)`:

  This method is the antithesis of the `start_watching` method, it is meant to
  undo any actions taken in calls to `start_watching` with the same cluster
  instance.  Once this is called, any updates to the set of member nodes of the
  cluster shouldn't update the cluster instance or set the `should_update` event.

* `report_up(self, service)`:

  This is one of the two methods used by the `lighthouse-reporter` script.  The
  single argument is a :class:`lighthouse.service.Service` instance.  This method
  should register the service as "up" to the discovery method such that any
  `lighthouse-writer` consumer processes will see the current node as up and
  configure their load balancers appropriately.

  This method should utilize the the :class:`lighthouse.node.Node` class and its
  `serialize()` function to send data about the service on the local node to
  the discovery method's system.

* `report_down(self, service)`:

  This method is the other of the two used by `lighthouse-reporter` and is the
  antithesis of the `report_up` method.  This method should tell the discovery
  method's system that the given service on the current node is no longer
  available.


.. _Zookeeper: https://zookeeper.apache.org
.. _`"CP" distributed systems`: http://en.wikipedia.org/wiki/CAP_theorem
