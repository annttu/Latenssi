#!/usr/bin/env python
# encoding: utf-8


from lib import rrd, config, config_utils, probe, web, probes
from time import sleep
import logging

config_utils.load_config()

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


def webdaemon():
    reloader = config_utils.ConfigReloader(start_pollers=False)
    reloader.start()
    try:
        web.webapp.run(host=str(config.bind_address), port=int(config.bind_port), reloader=bool(config.devel))
    except KeyboardInterrupt:
        pass
    reloader.stop()


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
