#!/usr/bin/env python
# encoding: utf-8

import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.WARN)

from lib import latenssi

if __name__ == '__main__':
    latenssi.webdaemon()