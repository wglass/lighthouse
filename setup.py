from setuptools import setup, find_packages

from lighthouse import __version__


classifiers = []
with open("classifiers.txt") as fd:
    classifiers = fd.readlines()


setup(
    name="lighthouse",
    version=__version__,
    description="Service discovery tool focused on ease-of-use and resiliency",
    author="William Glass",
    author_email="william.glass@gmail.com",
    url="http://github.com/wglass/lighthouse",
    license="MIT",
    classifiers=classifiers,
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
        "futures",
    ],
    extras_require={
        "redis": [],
        "docker": [
            "docker-py",
        ],
    },
    entry_points={
        "console_scripts": [
            "lighthouse-reporter = lighthouse.scripts.reporter:run",
            "lighthouse-writer = lighthouse.scripts.writer:run",
        ],
        "lighthouse.balancers": [
            "haproxy = lighthouse.haproxy.balancer:HAProxy",
        ],
        "lighthouse.discovery": [
            "zookeeper = lighthouse.zookeeper:ZookeeperDiscovery",
        ],
        "lighthouse.checks": [
            "http = lighthouse.checks.http:HTTPCheck",
            "tcp = lighthouse.checks.tcp:TCPCheck",
            "redis = lighthouse.redis.check:RedisCheck [redis]",
        ]
    },
    tests_require=[
        "nose",
        "mock",
        "coverage",
        "flake8",
    ],

)
