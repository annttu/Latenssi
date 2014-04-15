#!/usr/bin/env python
# encoding: utf-8


from lib import ping, rrd, config, probes
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
    for child in probes.probes:
        child.rrd.graph()


def daemon():
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
