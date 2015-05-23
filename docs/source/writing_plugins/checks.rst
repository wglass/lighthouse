Writing Health Check Plugins
============================

Health check plugins are the easiest of the three plugin types to write and
are liable to be the most common.  Writing a new health check plugin is a
simple matter of creating a :class:`lighthouse.check.Check` subclass and
exposing it via the `lighthouse.checks` entry point.

The key part of a health check plugin is the `perform()` method on the
subclass, it is where the actual checking takes place.  It's important
that this method take no arguments and returns `True` or `False` based
on the check's success.


Examples
~~~~~~~~

For an example of a check that has no external dependencies but uses custom
attributes and configuration, see the :class:`lighthouse.checks.http.HTTPCheck`
class included in the source distribution.

Likewise, for an example of a simple health check that involves external
dependencies see the :class:`lighthouse.checks.redis.RedisCheck` class.


Required Methods
~~~~~~~~~~~~~~~~

* `validate_dependencies(cls)` *(classmethod)*:

  This classmethod should check that all required external dependencies for
  your health check are met.

  If the requirements are met, this method should return True.  If not met
  it should return False.

* `validate_check_config(cls, config)` *(classmethod)*:

  The "config" argument to this classmethod is the dictionary representation
  of the health check's portion of the service YAML configuration, this method
  should validate any plugin-specific bits of that configuration.  The base
  :class:`lighthouse.check.Check` class automatically validates that the standard
  `host`, `port`, `rise` and `fall` values are present.

  If any parts of the configuration are invalid, a `ValueError` exception should
  be raised.

* `apply_check_config(self, config)`:

  This instance method's config argument is also the dictionary config of the
  health check's portion of a service's YAML config file, albeit one that has
  already been validated.

  This method should take the validated dictionary object and set any sort of
  attributes/state/etc. on the instance as necessary.

  .. warning::

     It it is *incredibly important* that this method be idempotent with regards
     to instances of your Check subclass.  Configurations can be altered at any
     time in any manner, sometimes with invalid values!  You want your plugin's
     state to reflect the contents of the YAML config file at all times.


* `perform()`:

  This method is the heart of the health check.  It performs the actual check
  and should return True if the health check passes and False if it fails.

  .. note::

    This method does not take any arguments, any sort of context required to
    perform the health check should be handled by applying the config and
    setting instance attributes.
