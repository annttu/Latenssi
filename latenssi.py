#!/usr/bin/env python
# encoding: utf-8

import logging
import sys
import argparse

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.WARN)

from lib import latenssi

def start_collector(args):
    latenssi.daemon()

def start_web(args):
    latenssi.webdaemon()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", default=False, action="store_true",
                        help="Turn debugging on")
    sp = parser.add_subparsers()
    collector = sp.add_parser("collector", help="Start collector")
    web = sp.add_parser("web", help="start web server")
    web.set_defaults(func=start_web)
    collector.set_defaults(func=start_collector)
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    args.func(args)
