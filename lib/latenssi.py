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
    for child in probes.probes:
        child.rrd.graph()


def html():
    """
    Generate html files
    """
    web.generate_pages()

def daemon():
    # Generate html files on startup
    html()
    for probe in probes.probes:
        p = probe.start()
        childs.append(p)

    try:
        while True:
            sleep(10)
    except Exception as e:
        pass

    for child in childs:
        try:
            child.stop()
        except Exception as e:
            logger.exception(e)
