API Meta-Cluster Example
========================

This example will demonstrate ACL-based routing where a single API is serviced
by multiple clusters, as well as the proxyies feature of the HAProxy balancer
plugin.

We'll have a redis-backed web API with two endpoints: one for "widgets" and one
for "sprockets".  Each endpoint will be served by a separate independent cluster
of webapp nodes.

The "sprockets" cluster will also communicate with a "partner" machine via a
cluster of proxy nodes.  Regardless of how many nodes there are in the sprockets
cluster and which nodes come and go, the only nodes to talk to the partner
are the proxy nodes.


.. image:: /static/api_cluster.png
    :align: center


Creating the partner "machine"
------------------------------

To start off with we'll launch a single instance of a "partner" container
meant to represent a 3rd-party API::

  $ ./launch.sh partner partnerapi

Naming the container "partnerapi" is important, the configuration on the proxy
cluster nodes will assume the "partner" is reachable via that name.

.. note::

    This "external" container is intentionally limited.  It doesn't make use
    lighthouse at all, and is only reachable by name from "proxy" nodes.

Creating the proxy cluster
--------------------------

The proxy cluster will be limited in numbers at first since in such a real-life
scenario the 3rd party partner will whitelist only certain IPs::

  $ ./launch.sh proxy proxy01


Naturally as this is just an example the cluster can be expanded to your heart's
content.

Proxy nodes don't run any extra services themselves, rather they configure their
HAProxy instances to proxy to the "partnerapi" machine.  If you connect to
proxy01 and look at the `/etc/haproxy.cfg` file you should see something along
the lines of::

  listen business_partner
	bind :7777
	mode http
	server partnerapi:88 partnerapi:88 maxconn 400


Creating the clusters
---------------------

To start off with we'll create two nodes for each of the cache, widgets and
sprockets clusters::

  $ ./launch.sh cache cache01
  $ ./launch.sh cache cache02
  $ ./launch.sh widgets widgets01
  $ ./launch.sh widgets widgets02
  $ ./launch.sh sprockets sprockets01
  $ ./launch.sh sprockets sprockets02

Once these containers are started you should see the widgets/sprockets nodes
show up in the HAProxy web interface of the client node:

.. image:: /static/meta_api_haproxy.png


The widgets API
---------------

The widgets API has one endpoint, "/api/widgets" that reponds to both GET and
POST requests.

A GET request shows a mapping of known widgets to their count, empty at first::

  $ curl http://<docker_ip>:<port>/api/widgets
  {
    "widgets": {}
  }

A POST to the endpoint requires a "widget" param set to any sort of string::

  $ curl -XPOST -d "widget=foo" http://<docker_ip>:<port>/api/widgets
  {
    "success": true
  }

With that "foo" widget added we can see the updated count::

  $ curl http://<docker_ip>:<port>/api/widgets
  {
    "widgets": {
      "foo": 1
    }
  }

After a few GET and POST requests, you can check the HAProxy web interface
on the client and see the traffic being balanced on the "api_widgets" backend.

The sprockets API
-----------------

The sprockets API is similar to widgets, it has a single endpoint that reponds
to both GET and POST requests but sprockets are shown as a set rather than
a mapping.

However, the sprockets API also talks to the "partner" API via the proxy
cluster.  Each response includes a "token" grabbed from the partner machine.

GET requests will show the set::

  $ curl http://<docker_ip>:<port>/api/sprockets
  {
    "token": "8c53bb14-92ad-4722-aa07-181aeddcfb94",
    "sprockets" []
  }

POST requests require a "sprocket" param and will add a new sprocket to
the set::

  $ curl -XPOST -d"sprocket=bar" http://<docker_ip>:<port>/api/sprockets
  {
    "success": true,
    "token": "76a11362-d26d-496f-b981-ba864aa68877"
  }
  $ curl http://<docker_ip>:<port>/api/sprockets
  {
    "token": "d7ee21c7-3a6f-4fc2-a1fe-0d62321bba4e",
    "sprockets" [
      "bar"
    ]
  }

And there you have it!  A series of horizontally scalable clusters that
communicates with an "external" service, proxied in such a way that the
external service only sees one machine talking to it.
