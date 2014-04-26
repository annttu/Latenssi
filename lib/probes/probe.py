#!/usr/bin/env python
# encoding: utf-8

"""
Probe template class
"""

from lib import config, thread

import subprocess
import logging
import re
import time

logger = logging.getLogger("probe")

class Probe(thread.Thread):
    def __init__(self, target):
        thread.Thread.__init__(self)
        self.target = target
        self.name = "%s-%s" % (self._name.lower(), target.replace(".", "_"))
        self.title = "%s %s" % (self._name, target)
        self._throttle_limit = 1.0
        self._throttle_time = 1

    def graphs(self):
        return [self.name]

