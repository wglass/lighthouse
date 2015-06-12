import inspect
import re

import lighthouse.balancer
import lighthouse.check
import lighthouse.checks.http
import lighthouse.cluster
import lighthouse.configs.handler
import lighthouse.configs.monitor
import lighthouse.configs.watcher
import lighthouse.configurable
import lighthouse.discovery
import lighthouse.haproxy.balancer
import lighthouse.haproxy.config
import lighthouse.haproxy.control
import lighthouse.haproxy.stanzas.section
import lighthouse.haproxy.stanzas.stanza
import lighthouse.haproxy.stanzas.meta
import lighthouse.haproxy.stanzas.frontend
import lighthouse.haproxy.stanzas.backend
import lighthouse.haproxy.stanzas.peers
import lighthouse.haproxy.stanzas.proxy
import lighthouse.haproxy.stanzas.stats
import lighthouse.log
import lighthouse.node
import lighthouse.peer
import lighthouse.pluggable
import lighthouse.reporter
import lighthouse.service
import lighthouse.writer
import lighthouse.zookeeper
import lighthouse.events
import lighthouse.redis.check


modules_to_test = (
    lighthouse.balancer,
    lighthouse.check,
    lighthouse.checks.http,
    lighthouse.cluster,
    lighthouse.configs.handler,
    lighthouse.configs.monitor,
    lighthouse.configs.watcher,
    lighthouse.configurable,
    lighthouse.discovery,
    lighthouse.haproxy.balancer,
    lighthouse.haproxy.config,
    lighthouse.haproxy.control,
    lighthouse.haproxy.stanzas.section,
    lighthouse.haproxy.stanzas.stanza,
    lighthouse.haproxy.stanzas.meta,
    lighthouse.haproxy.stanzas.frontend,
    lighthouse.haproxy.stanzas.backend,
    lighthouse.haproxy.stanzas.peers,
    lighthouse.haproxy.stanzas.proxy,
    lighthouse.haproxy.stanzas.stats,
    lighthouse.log,
    lighthouse.node,
    lighthouse.peer,
    lighthouse.pluggable,
    lighthouse.reporter,
    lighthouse.service,
    lighthouse.writer,
    lighthouse.zookeeper,
    lighthouse.events,
    lighthouse.redis.check,
)


def test_docstrings():
    for module in modules_to_test:
        for path, thing in get_module_things(module):
            yield create_docstring_assert(path, thing)


def get_module_things(module):
    module_name = module.__name__

    for func_name, func in get_module_functions(module):
        if inspect.getmodule(func) != module:
            continue
        yield (module_name + "." + func_name, func)

    for class_name, klass in get_module_classes(module):
        if inspect.getmodule(klass) != module:
            continue
        yield (module_name + "." + class_name, klass)

        for method_name, method in get_class_methods(klass):
            if method_name not in klass.__dict__:
                continue
            yield (module_name + "." + class_name + ":" + method_name, method)


def get_module_classes(module):
    for name, klass in inspect.getmembers(module, predicate=inspect.isclass):
        yield (name, klass)


def get_module_functions(module):
    for name, func in inspect.getmembers(module, predicate=inspect.isfunction):
        yield (name, func)


def get_class_methods(klass):
    for name, method in inspect.getmembers(klass, predicate=inspect.ismethod):
        yield (name, method)


def create_docstring_assert(path, thing):

    def test_function():
        assert_docstring_present(thing, path)
        # TODO(wglass): uncomment this assert and fill out the param info
        # for methods and functions
        # assert_docstring_includes_param_metadata(thing, path)

    test_name = "test_docstring__%s" % de_camelcase(path)
    test_function.__name__ = test_name
    test_function.description = test_name

    return test_function


def assert_docstring_present(thing, path):
    # TODO(wglass): remove this check for __init__ when the param metadata
    # assert is re-enabled
    if path.endswith("__init__"):
        return

    docstring = inspect.getdoc(thing)
    if not docstring or not docstring.strip():
        raise AssertionError("No docstring present for %s" % path)


def assert_docstring_includes_param_metadata(thing, path):
    if inspect.isclass(thing):
        return

    docstring = inspect.getdoc(thing)
    if not docstring:
        return

    for arg_name in inspect.getargspec(thing).args:
        if arg_name in ("self", "cls"):
            continue

        if ":param %s:" % arg_name not in docstring:
            raise AssertionError(
                "Missing :param: for arg %s of %s" % (arg_name, path)
            )
        if ":type %s:" % arg_name not in docstring:
            raise AssertionError(
                "Missing :type: for arg %s of %s" % (arg_name, path)
            )


first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def de_camelcase(name):
    return all_cap_re.sub(
        r'\1_\2',
        first_cap_re.sub(r'\1_\2', name)
    ).lower()
