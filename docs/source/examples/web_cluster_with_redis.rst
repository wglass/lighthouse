Simple Web Cluster Example
==========================

In this example we'll construct a simple system with two clusters: a webapp
cluster serving up some basic content and a cache redis cluster used in creating
said content.

.. image:: /static/simple_example.png
    :align: center

Creating the cache cluster
~~~~~~~~~~~~~~~~~~~~~~~~~~

To start off with we'll launch a couple cache nodes to create the redis
cluster::

  $ ./launch.sh cache cache01

  $ ./launch.sh cache cache02

Two should be fine for our purposes.

.. warning::

   These redis instances are independent, if a request ends up using a different
   cache than a previous one the results will be inconsistent!  This is OK here
   since this is a simple example but in the real world you'll need to be mindful
   of how requests are routed to stateful clusters.


Creating the web cluster
~~~~~~~~~~~~~~~~~~~~~~~~

Spinning up a webapp node is a simple matter::

  $ ./launch.sh webapp app01

In this part of the example we'll show off a particular feature of lighthouse:
handling multiple instances of the same service on a single host.  To bring
up such a node::

  $ ./launch.sh multiapp app02

This "multiapp" container will have two instances of the webapp process running,
each on different ports but reporting as part of the same cluster.

With these two launched you should see three entries in the "webapp" section
of the client container's HAProxy web interface:

.. image:: /static/webapp_haproxy.png

Two hosts, three nodes.

Sending traffic
~~~~~~~~~~~~~~~

Now that our clusters are up and discovered it's time to send traffic to them.
First off we need to know which port the client image's "8000" port mapped to.
This can be done with a simple `docker ps` command::

  $ docker ps
  CONTAINER ID        IMAGE                                 COMMAND                CREATED             STATUS              PORTS                                                                                                                         NAMES
  6d6db2e1842e        lighthouse.examples.client:latest     "/bin/sh -c 'supervi   13 minutes ago      Up 13 minutes       0.0.0.0:33270->1024/tcp, 0.0.0.0:33271->8000/tcp, 0.0.0.0:33272->8080/tcp, 0.0.0.0:33273->9000/tcp, 0.0.0.0:33274->9009/tcp   client
  82618a6a2fef        lighthouse.examples.zk:latest         "/opt/zookeeper/bin/   28 hours ago        Up 28 hours         2181/tcp, 2888/tcp, 3888/tcp                                                                                                  zk01
  ...

Under the "PORTS section we find "0.0.0.0:33272->8080/tcp", so in this example
the mapped port is "33274".

So a curl to `http://<docker host ip>:33274/` would yield:

.. code-block:: html

  <h1>Current count: 1</h1>


With each subsequent request the counter will update, and HAProxy will balance
the requests amont the three webapp nodes.

Going further
~~~~~~~~~~~~~

This example showed how a very basic set of clusters can be set up, but it
doesn't have to end there!  Try:

  * killing and spinning up nodes to each cluster and watch the HAProxy web
    interface to see how it reacts

  * taking a node down while blasting the cluster with traffic via tools
    like ApacheBench_

  * removing all nodes from the cache cluster while watching the reporting
    logs from the webapp nodes


.. _ApacheBench: https://httpd.apache.org/docs/2.2/programs/ab.html
