Configuring Zookeeper
======================


The Zookeeper_ discovery method config is incredibly simple, there are two
settings and they are both required.

Settings
~~~~~~~~~

* **hosts** *(required)*:

  A list of host strings.  Each host string should include the hostname and
  port, separated by a colon (":").

* **path** *(required)*:

  A string setting denoting the base path to use when looking up or reporting
  on node availability.  For example, a path of `/lighthouse/services` would
  mean that any services available would be found at the path
  `/lighthouse/services/service_name`.

.. warning::

   Altering the "path" setting is doable, but should be avoided if at all
   possible.  Whathever provisioning method is used to update the
   ``zookeeper.yaml`` file is almost certainly going to leave many nodes out of
   sync at least for a time.  A situation where nodes don't agree on where to
   look for each other is indistinguishable from a large network outage.


Example
~~~~~~~

A simple example with a three-member zookeeper cluster and a base path:


`discovery/zookeeper.yaml`

.. code-block:: yaml

   hosts:
     - "zk01:2181"
     - "zk02:2181"
     - "zk03:2181"
   path: "/lighthouse/services"


.. _Zookeeper: https://zookeeper.apache.org
