#!/usr/bin/env python
# encoding: utf-8


from lib import rrd, config, probe, web, probes
import settings

from time import sleep

setting_vars = vars(settings)
config.load_config(setting_vars)
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

def daemon():
    # Generate html files on startup
    html()
    childs = []
    for p in probe.probes:
        childs.append(p)

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
