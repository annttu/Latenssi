#!/usr/bin/env python
# encoding: utf-8

import logging
import sys
import argparse

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.WARN)

from lib import latenssi

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", default=False, action="store_true",
                        help="Turn debugging on")
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    latenssi.daemon()
