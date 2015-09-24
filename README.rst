Lighthouse Service Discovery Tool
===================================

.. image::
    https://travis-ci.org/wglass/lighthouse.svg?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/wglass/lighthouse
.. image::
    https://codeclimate.com/github/wglass/lighthouse/badges/gpa.svg
    :alt: Code Climate
    :target: https://codeclimate.com/github/wglass/lighthouse
.. image::
    https://readthedocs.org/projects/lighthouse/badge/?version=0.15.1
    :alt: Documentation Status
    :target: https://readthedocs.org/projects/lighthouse/?badge=0.15.1

Lighthouse is a service node discovery system written in python, built with
resilience, flexibility and ease-of-use in mind and inspired by Airbnb's
SmartStack_ solution.  Out of the box it supports discovery via Zookeeper_ with
cluster load balancing handled by an automatically configured HAProxy_.

Documentation
~~~~~~~~~~~~~~

More detailed documentation can be found on `Read the Docs`_.

Overview
~~~~~~~~~

A lighthouse setup consists of three parts running locally on each node: a load
balancer, the `lighthouse-writer` script and (usually) the `lighthouse-reporter`
script.

.. image::
   http://lighthouse.readthedocs.org/en/latest/_images/soa_node.png
   :alt: Diagram of a node
   :align: center

In a Lighthouse setup, no node's application code is aware of the existence of
other nodes, they talk to a local port handled by an instance of the load
balancer which in turn routes traffice among the various known other nodes.

This local load balancer is automatically updated when nodes come and go
via the `lighthouse-writer` script, which talks to the discovery method (e.g.
Zookeeper) to keep track of which nodes on which clusters are up.

The `lighthouse-reporter` script likewise talks to the discovery method, it
it is responsible for running health checks on any services on the local
node and reports to the discovery method that the healthy services are up
and the unhealthy ones are down.


Development
~~~~~~~~~~~~~
The code is hosted on GitHub_

To file a bug or possible enhancement see the `Issue Tracker`_, also found
on GitHub.


License
~~~~~~~~
\(c\) 2014-2015 William Glass

Lighthouse is licensed under the terms of the MIT license.  See the LICENSE_
file for more details.

.. _`Read the Docs`: http://lighthouse.readthedocs.org/
.. _SmartStack: http://nerds.airbnb.com/smartstack-service-discovery-cloud/
.. _Zookeeper: https://zookeeper.apache.org
.. _HAProxy: http://www.haproxy.org
.. _GitHub: https://github.com/wglass/lighthouse
.. _`Issue Tracker`: https://github.com/wglass/lighthouse/issues
.. _LICENSE: https://github.com/wglass/lighthouse/blob/master/LICENSE
