#!/usr/bin/env python
# encoding: utf-8

# Script to generate static graph images.
# Use for example with cron
#
# Not needed if dynamic_graphs is enabled!

from lib import latenssi

if __name__ == '__main__':
    latenssi.graph()

