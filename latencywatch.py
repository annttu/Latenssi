#!/usr/bin/env python
# encoding: utf-8


from lib import ping, rrd, config
import settings

from time import sleep
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


if __name__ == '__main__':

    vars = vars(settings)

    for k,v in vars.items():
        if k.startswith('_'):
            continue
        setattr(config,k,v)

    childs = []

    for probe in settings.probes:
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
