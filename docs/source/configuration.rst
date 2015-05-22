Configuration
---------------

The lighthouse scripts are configured by passing in a root config directory which
contains individual YAML_ config files and follows a certain layout::

    <config dir>/
      |____haproxy.yaml
      |____discovery/
      |      |____zookeeper.yaml
      |____clusters/
      |      |____webcache.yaml
      |      |____pg-db.yaml
      |      |____users-api.yaml
      |____services/
      |      |____a_service.yaml
      |      |____other_service.yaml


There are four types of config file:

* **balancer**:

  Files that configure the locally-running load balancer(s).  These live in the
  root of the config directory. The project includes a plugin for HAProxy as a
  balancer.

  :doc:`configuration/haproxy`

* **discovery**:

  Discovery config files live in a ``discovery`` subdirectory, each
  file configures a single discovery method with a name matching the filename.
  The project includes a plugin for Zookeeper as a discovery method.

  :doc:`configuration/zookeeper`

* **cluster**:

  Cluster config files are found under the ``clusters`` subdirectory and denote
  services used by the local machine/node that should be watched for member
  node updates.

  :doc:`configuration/clusters`

* **service**:

  Each config file under the ``services`` subdirectory represents a local service
  to be reported as up or down via the discovery method(s).  These files include
  configurations for a service's health checks as well.  The project includes
  simple HTTP and Redis health checks.

  :doc:`configuration/services`

.. note::
   **Service vs. Cluster terminology**: Think of a "service" as used in this
   documentation as describing an individual service *provided* by the local
   node/machine, a "cluster" as a description of a service *consumed* by the local
   node/machine.

.. toctree::
   :hidden:
   :maxdepth: 1

   configuration/haproxy
   configuration/zookeeper
   configuration/clusters
   configuration/services

.. _YAML: http://yaml.org
