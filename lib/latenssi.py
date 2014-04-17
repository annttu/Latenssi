#!/usr/bin/env python
# encoding: utf-8


from lib import ping, rrd, config, probes, web
import settings

from time import sleep
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

setting_vars = vars(settings)
config.load_config(setting_vars)
probes.populate()

def graph():
    """
    Generate static graphs
    """
    for interval_name, interval in config.intervals.items():
        for child in probes.probes:
            rrd.RRD.graph(child.name, interval=interval_name)


def html():
    """
    Generate html files
    """
    web.generate_pages()

def daemon():
    # Generate html files on startup
    html()
    childs = []
    for probe in probes.probes:
        childs.append(probe)

    childs.append(rrd.RRD)

    for child in childs:
        child.start()

    try:
        while True:
            sleep(10)
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        pass


    for child in childs:
        try:
            child.stop()
        except Exception as e:
            logger.error("Cannot stop child")
            logger.exception(e)
