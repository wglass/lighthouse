Writing Plugins
===============

Lighthouse relies on a plugin system for it's functionality.  All load balancers,
discovery methods and health checks are plugins, even the included ones!

All that's required for creating a new plugin is to subclass the proper base
class and add that subclass to the proper entry point in your project's setup.

For example a new health check called "mycheck" might have a class called
`MyCheck`, a subclass of :class:`lighthouse.check.Check` and added to a
`setup.py`'s setup() call:

`setup.py`

.. code-block:: python

  from setuptools import setup

  setup(
      # basics...
      install_requires=[
        # dependencies for your plugin go here
      ],
      entry_points={
          "lighthouse.checks": [
              mycheck = myproject.MyCheck
          ]
      }
  )

Each of the three plugin types have their own entrypoint.  For details of each of
the three plugin types see their individual documentation:

* :doc:`writing_plugins/checks`

* :doc:`writing_plugins/discovery_methods`

* :doc:`writing_plugins/balancers`


.. toctree::
   :hidden:

   Health Checks <writing_plugins/checks>
   Discovery Methods <writing_plugins/discovery_methods>
   Load Balancers <writing_plugins/balancers>
