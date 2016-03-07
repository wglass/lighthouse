Lighthouse Service Discovery Tool
=================================

.. image::
    https://img.shields.io/pypi/v/lighthouse.svg
    :target: http://pypi.python.org/pypi/lighthouse
    :alt: Python Package Version
.. image::
    https://readthedocs.org/projects/lighthouse/badge/?version=latest
    :alt: Documentation Status
    :target: http://lighthouse.readthedocs.org/en/latest/
.. image::
    https://travis-ci.org/wglass/lighthouse.svg?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/wglass/lighthouse
.. image:: https://landscape.io/github/wglass/lighthouse/master/landscape.svg?style=flat
   :alt: Code Health
   :target: https://landscape.io/github/wglass/lighthouse/master
.. image::
    https://codecov.io/github/wglass/lighthouse/coverage.svg?branch=master
    :alt: Codecov.io
    :target: https://codecov.io/github/wglass/lightouse?branch=master

Lighthouse is a service node discovery system written in python, built with
resilience, flexibility and ease-of-use in mind and inspired by Airbnb's
SmartStack_ solution.  Out of the box it supports discovery via Zookeeper_ with
cluster load balancing handled by an automatically configured HAProxy_.

To dive right in, checkout the `Getting Started`_ page in the docs.

Overview
~~~~~~~~

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

Documentation
~~~~~~~~~~~~~

More detailed documentation can be found on `Read the Docs`_.


Development
~~~~~~~~~~~

The code is hosted on GitHub_

To file a bug or possible enhancement see the `Issue Tracker`_, also found
on GitHub.


License
~~~~~~~

\(c\) 2014-2016 William Glass

Lighthouse is licensed under the terms of the Apache license (2.0).  See the
LICENSE_ file for more details.

.. _`Getting Started`: http://lighthouse.readthedocs.org/en/latest/getting_started.html
.. _`Read the Docs`: http://lighthouse.readthedocs.org/
.. _SmartStack: http://nerds.airbnb.com/smartstack-service-discovery-cloud/
.. _Zookeeper: https://zookeeper.apache.org
.. _HAProxy: http://www.haproxy.org
.. _GitHub: https://github.com/wglass/lighthouse
.. _`Issue Tracker`: https://github.com/wglass/lighthouse/issues
.. _LICENSE: https://github.com/wglass/lighthouse/blob/master/LICENSE
