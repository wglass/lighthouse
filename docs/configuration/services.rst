Configuring Services
=====================

Service configs have more required settings than most other configurable items,
but are still fairly easy to define.  Each service config must define the port
to use for communicating with the service, as well as the discovery method used
for reporting and the health checks to use to determine the service's
availability.

For example, a simple redis cache service:

`services/cache.yaml`

.. code-block:: yaml

    port: 6379
    discovery: "zookeeper"
    host: "127.0.0.1"
    checks:
      interval: 3
      redis:
        rise: 2
        fall: 1

This service runs on the default redis port of 6379, uses the
:doc:`Zookeeper discovery <zookeeper>` method and the redis health check.  The
check is performed every three seconds, the check would have to pass twice for
the service to be considered "up" and fail only once to be considered "down".


Settings
~~~~~~~~

* **port**/**ports** *(required)*:

  Port(s) that the local service is listening on.  If listing multiple ports,
  the `ports` setting must be used.  For single-port services either `port`
  or `ports` (with a single entry) will do.

* **discovery** *(required)*:

  Discovery method to use when reporting the local node's service(s) as up or
  down.

* **checks** *(required)*:

  A list of health checks to perform, which will determine if a service is up
  or not.

* **host**:

  Optional hostname to use when communicating with the service.  Usually
  "localhost" or "0.0.0.0", defaults to "127.0.0.1" if not specified.

* **metadata**:

  An optional mapping of data to send along when reporting the service as up
  and available.  Useful for providing extra context about a node for use in
  a balancer plugin (e.g. denoting a "master" or "slave" node).


Health Check Settings
~~~~~~~~~~~~~~~~~~~~~

* **interval** *(required)*:

  The time (in seconds) to wait between each health check.  This setting belongs
  under the "checks" setting.

* **rise** *(required)*:

  The number of successful health checks that must happen in a row for the
  service to be considered "up".  This setting belongs under individual health
  check configs.

* **fall** *(required)*:

  The number of failed health checks that must happen in a row for the service to
  be considered "down".  This setting belongs under individual health check
  configs.


Included Health Checks
~~~~~~~~~~~~~~~~~~~~~~

The Lighthouse project comes bundled with a handful of health checks by default,
including two basic ones for HTTP-based services and lower-level TCP services.


HTTP
^^^^

The HTTP health check performs a simple request to a given uri and passes if
the response code is in the 2XX range.  The HTTP health check has no extra
dependencies but does have a required extra setting:

* **uri** *(required)*:

  The uri to hit with an HTTP request to perform the check (e.g. "/health")

TCP
^^^

The TCP health check can be used for services that don't use HTTP to communicate
(e.g. redis, kafka, etc.).  The health check is configured to have a "query"
message sent to the service and an expected "response".

* **query** *(required)*:

  The message to send to the port via TCP (e.g. Zookeeper's "ruok")

* **response** *(required)*

  Expected response from the service.  If the service responds with a different
  message or an error happens during the process the check will fail.


Optional Health Checks
~~~~~~~~~~~~~~~~~~~~~~


Redis
^^^^^

Sends the "PING" command to the redis instance and passes if the proper "PONG"
response is received.  The Redis health check plugin has no extra config
settings.  This optional plugin requires Lighthouse to be installed with the
"redis" extra::

  pip install lighthouse[redis]
