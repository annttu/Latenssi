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


    for child in settings.probes:
        child.rrd.graph()

