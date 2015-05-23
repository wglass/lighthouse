Examples
========

Example use-cases of lighthouse live in the `examples` directory.  There are a
handful of Docker_ images with various lighthouse setups that can be launched
to create small clusters.

Each example also makes use of a "client" container that consumes the resulting
services and exposes requisite ports that can be hit to show off just how the
clusters handle traffic.

Examples List
-------------


.. toctree::
   :maxdepth: 1
   :glob:

   Simple Web Cluster <examples/web_cluster_with_redis>
   API Meta-Cluster <examples/api_meta_cluster_with_proxies>


Setting Up
----------

To start with you'll need Docker set up properly.  How to do that depends on
your OS and is beyond the scope of this documentation but luckily the folks at
Docker `provide some of their own`_.

Once you have docker up and running, creating the example images is as simple as::

  make

This shouldn't take *too* long, and once it's done you should have a handful of
example docker images with names starting with "lighthouse.examples"::

  [examples] $ docker images

  REPOSITORY                      TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
  lighthouse.examples.client      latest              1bc85bf377a7        52 minutes ago      436.4 MB
  lighthouse.examples.sprockets   latest              e8674c42d7bc        52 minutes ago      451.2 MB
  lighthouse.examples.widgets     latest              f449a383522b        52 minutes ago      451.2 MB
  lighthouse.examples.multiapp    latest              684fb9de9298        52 minutes ago      451.2 MB
  lighthouse.examples.webapp      latest              7ab84d42ddcd        52 minutes ago      451.2 MB
  lighthouse.examples.cache       latest              464a3b360d4d        52 minutes ago      449 MB
  lighthouse.examples.base        latest              d990927b27e4        54 minutes ago      434.4 MB
  lighthouse.examples.zk          latest              c31155053d47        2 days ago          342.7 MB
  ...


First Steps
-----------

There are some common components to each example that should be set up first,
namely a client container and the Zookeeper_ discovery method.

Launching Zookeeper
~~~~~~~~~~~~~~~~~~~

The zookeeper host in the cluster is expected to be named `zk01` and use the
standard ports, so it can be launched with::

  $ docker run --name zk01 -d lighthouse.examples.zk


Launching a Client
~~~~~~~~~~~~~~~~~~

Launching a client container is a simple matter of using the included
`launch.sh` helper script found in the `examples` directory::

  $ ./launch.sh client client

Details about the script can be found in the `launching`_ section.

Individual Nodes
----------------

Launching
~~~~~~~~~

Launching a new node can be done by hand via docker, but the `examples`
directory includes a handy `launch.sh` script to make things easier::

  $ ./launch.sh <type> <name>

Where the "<type>" matches the end of the example docker image name.  For
example the "lighthouse.examples.webapp" image's node type is "webapp".

The "<name>" portion is any host name you want to give to the node.  Since
this is an SOA and nodes are (hopefully) automatically discovered the name
doesn't really matter and is mostly for convenience.

Examining
~~~~~~~~~

Each node container exposes two web interface ports for examining what exactly
is going on: one for HAProxy and one for Supervisord_, the process management
tool used to run multiple processes at once in a single container.  The HAProxy
web interface listens on port 9009 with the URI "/haproxy", the supervisord web
interface listens on port 9000.

To avoid conflicting port assignments, a container will map these ports to a
random available one on the docker host.  To see the resulting mapped port
you'll have to run `docker ps`::

  $ docker ps

  CONTAINER ID        IMAGE                              COMMAND                CREATED             STATUS              PORTS                                                                                                NAMES
  aa037622260e        lighthouse.examples.cache:latest   "/bin/sh -c 'supervi   3 seconds ago       Up 2 seconds        0.0.0.0:32768->1024/tcp, 0.0.0.0:32769->6379/tcp, 0.0.0.0:32770->9000/tcp, 0.0.0.0:32771->9009/tcp   cache01
  85890f46dc8f        lighthouse.examples.zk:latest      "/opt/zookeeper/bin/   17 seconds ago      Up 16 seconds       2181/tcp, 2888/tcp, 3888/tcp                                                                         zk01

In this example, the "cache01" container's HAProxy web interface can be accessed
via `http://<docker_host_ip>:32771/haproxy` and the supervisord web interface
via `http://<docker_host_ip>:32770`.

Connecting
~~~~~~~~~~

Along with the `launch.sh` script there's also a handy `connect.sh` script::

  $ ./connect.sh <name>

This will attach to the container with the "<name>" name and run an
interactive bash session, helpful for examining log and configuration files
by hand.  Note that the TERM environment variable is not set by default so
many things like `less` and `clear` might not work quite right unless it's
set by hand.

For each node the lighthouse scripts run in debug mode and log quite a bit.
The log files for the lighthouse script live under
`/var/log/supervisor/lighthouse` in the container.  The services served up
by containers will generally put their logs under `/var/log/supervisor/`.

The HAProxy config is written to `/etc/haproxy.cfg`.

Stopping
~~~~~~~~

Unlike launching or connecting, there is no helper script as a simple docker
command does the job::

  $ docker rm -f <name>

This will halt the node container and unregister it from zookeeper
automatically.


.. _Docker: https://docker.com
.. _`provide some of their own`: https://docs.docker.com/installation/#installatio
.. _Zookeeper: https://zookeeper.apache.org
.. _Supervisord: http://supervisord.org
