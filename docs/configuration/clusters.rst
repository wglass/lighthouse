Configuring Clusters
=====================

Cluster configs are very simple, all that's needed is a discovery method defined
by the key `discovery` and a section specific to the load balancer in use.

A simple web server example:

`clusters/webapp.yaml`

.. code-block:: yaml

    discovery: "zookeeper"
    haproxy:
      port: 8000
      frontend:
        - "log global"
      backend:
        - "mode http"

In this example we're using the Zookeeper discovery method and the HAProxy load
balancer.  The balancer should listen locally on port 8000 and the HAProxy
frontend definition should include the `log global` directive and the backend
definition should include the `mode http` directive.


Meta-Clusters
~~~~~~~~~~~~~

In some use-cases a service might actually be composed of several clusters, with
special rules for routing between them.  For example, a RESTful api that routes
based on URL where `/api/widgets` hits the "widgets" cluster and `/api/sprockets`
hits the "sprockets" cluster.

To do this, the widget and sprocket cluster configs would use the `meta_cluster`
setting and provide the "ACL" rule for how they're routed.

`clusters/widgets.yaml`

.. code-block:: yaml

    discovery: "zookeeper"
    meta_cluster: "webapi"
    haproxy:
      acl: "path_beg /api/widgets"
      backend:
        - "mode http"

`clusters/sprockets.yaml`

.. code-block:: yaml

    discovery: "zookeeper"
    meta_cluster: "webapi"
    haproxy:
      acl: "path_beg /api/sprockets"
      backend:
        - "mode http"
        - "maxconn 500"  # maybe the sprockets cluster is on limited hardware

You'll note that neither of these actually list which port for the load balancer
to listen on.  Rather than have each cluster config list a port and hope they
match, we set the port via the `meta_clusters` setting in the load balancer
config.


`haproxy.yaml`

.. code-block:: yaml

  config_file: "/etc/haproxy.cfg"
  socket_file: "/var/run/haproxy.sock"
  pid_file: "/var/run/haproxy.pid"
  meta_clusters:
    webapi:
      port: 8888
      frontend:
        - "mode http"

This will tell HAProxy to listen on port 8888 locally and serve up the
meta-service, where requests to `/api/widgets` hit the widgets cluster and
requests to `/api/sprockets` get routed to an independent sprockets cluster.

Note that it also adds the "mode http" directive to the meta cluster's frontend
definition, a requirement for "path_beg" ACLs.  The "frontend" portion of a
`meta_clusters` is a list of any frontend directives that should be added to
the meta cluster's stanza.

Settings
~~~~~~~~~

* **discovery** *(required)*:

  The name of the discovery method to use for determining available nodes.

* **meta_cluster**:

  Name of the "meta cluster" this cluster belongs to.  Care must be taken such
  that the meta cluster has a port set in the load balancer config file.


HAProxy Settings
~~~~~~~~~~~~~~~~~

The following settings are available for the `haproxy` setting of a cluster.


*  **port**:

   Specifies which port the local load balancer should bind to for communicating
   to the cluster.  Not applicable to meta-clusters.

*  **acl**:

   Defines the ACL routing rule for a cluster who is a member of a meta-cluster.
   Not applicable to regular non-meta clusters.

*  **frontend**:

   Custom HAProxy config lines for the frontend stanza generated for the
   cluster.  Lines are validated to make sure the directive is a legal one for
   a frontend stanza but other than that anything goes.

*  **backend**:

   Custom HAProxy config lines for the backend stanza generated for the
   cluster.  Lines are validated to make sure the directive is a legal one for
   a backend stanza but other than that anything goes.

*  **server_options**:

   Extra options to add to a node's `server` directive within a backend stanza.
   (e.g. `slowstart` if nodes in the cluster should have their traffic share
   ramped up gradually)
