#!/usr/bin/env python
# encoding: utf-8

import sys
from lib import rrd, config, config_utils, probe, web, probes, exceptions
from time import sleep
import logging

try:
    config_utils.load_config()
except exceptions.ConfigError as e:
    print(e)
    sys.exit(1)


from lib.routes import *

logger = logging.getLogger("Latenssi")


probe.populate()


def graph():
    """
    Generate static graphs
    """
    for interval_name, interval in config.intervals.items():
        for child in probe.probes:
            for graph in child.graphs():
                rrd.RRD.graph(graph, interval=interval_name)


def html():
    """
    Generate html files
    """
    web.generate_pages()


def get_webdaemon():
    reloader = config_utils.ConfigReloader(start_pollers=False)
    reloader.start()
    return web.webapp


def webdaemon(run=True):
    d = get_webdaemon()
    try:
        d.run(host=str(config.bind_address), port=int(config.bind_port), reloader=bool(config.devel))
    except KeyboardInterrupt:
        pass


def daemon():
    childs = []
    for p in probe.probes:
        childs.append(p)

    childs.append(rrd.RRD)

    for child in childs:
        child.start()

    reloader = config_utils.ConfigReloader()
    reloader.start()
    childs.append(reloader)

    try:
        while True:
            sleep(5)
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        logger.exception("Unhandled exception")


    for child in childs:
        try:
            child.stop()
        except Exception as e:
            logger.error("Cannot stop child")
            logger.exception(e)
