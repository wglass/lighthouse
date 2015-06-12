Getting Started
===============

Installation
--------------

Automatic
~~~~~~~~~~

Lighthouse is available via PyPI_, installation is as easy as::

    pip install lighthouse


Note that when installed this way the example files found in the source repo are
not included.  If you wish to use the examples, a manual install via the current
source tarball is your best choice.


Manual
~~~~~~~

First download the current tarball at :current_tarball:`z`, then:

.. parsed-literal::

    tar -zxvf lighthouse-|version|.tar.gz
    cd lighthouse-|version|
    python setup.py install


Prerequisites
--------------

**Python verison**: Lighthouse runs on python versions 2.6 and greater, but is
better vetted on 2.7 and 3.4 specifically.  Versions 2.6 and PyPy_ are included
in the test suite but are less rigorously tested manually.

**Required libraries**: By default the lighthouse installation depends on

* Watchdog_ for monitoring changes to config files
* PyYAML_ to parse the config files
* Kazoo_ to communicate with Zookeeper
* Six_ to maintain python 2 and 3 compatibility

**HAProxy**: As of right now only HAProxy version 1.4 or higher, 1.3 *might* work
but is untested.

**Platforms**: Lighthouse is most extensively tested on Linux and Mac OSX but
should run just fine on any Unix-y/POSIX platform.  Native windows use is
unsupported as UNIX sockets are required to control the load balancer, but a
setup with cygwin is theoretically possible.


Optional Extras
---------------

Redis plugins
~~~~~~~~~~~~~

Lighthouse includes a "redis" extra package that comes with a health check for
redis services.  To install an extra, use square brackets when installing
lighthouse::

  pip install lighthouse[redis]


Examples
--------

At this point you should be ready to run the examples if you've downloaded
them.  Simply run the ``start.sh`` script for the target example and then run
``lighthouse-writer`` and ``lighthouse-reporter`` passing in the path to the
example directory.  For more details on the included examples see
:doc:`examples`.


Configuration
-------------

The next step will of course be customizing your own :doc:`configuration`.


.. _PyPI: http://pypi.python.org/pypi/lighthouse
.. _PyPy: http://pypy.org
.. _Watchdog: https://pythonhosted.org/watchdog/
.. _PyYAML: http://pyyaml.org
.. _Kazoo: https://kazoo.readthedocs.org
.. _Six: https://pythonhosted.org/six/
