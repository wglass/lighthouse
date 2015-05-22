from setuptools import setup, find_packages

from lighthouse import __version__


setup(
    name="lighthouse",
    version=__version__,
    description="Service discovery tool focused on ease-of-use and resiliency",
    author="William Glass",
    author_email="william.glass@gmail.com",
    url="http://github.com/wglass/lighthouse",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    package_data={
        "lighthouse": ["haproxy/*.json"],
    },
    install_requires=[
        "watchdog",
        "pyyaml",
        "kazoo",
        "six",
    ],
    entry_points={
        "console_scripts": [
            "lighthouse-reporter = lighthouse.scripts.reporter:run",
            "lighthouse-writer = lighthouse.scripts.writer:run"
        ],
        "lighthouse.balancers": [
            "haproxy = lighthouse.haproxy.balancer:HAProxy",
        ],
        "lighthouse.discovery": [
            "zookeeper = lighthouse.zookeeper:ZookeeperDiscovery",
        ],
        "lighthouse.checks": [
            "http = lighthouse.checks.http:HTTPCheck",
            "redis = lighthouse.checks.redis:RedisCheck",
        ]
    },
    tests_require=[
        "nose",
        "mock",
        "coverage",
        "flake8",
    ],
)
