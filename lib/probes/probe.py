#!/usr/bin/env python
# encoding: utf-8

"""
Probe template class
"""

from lib import config, thread, utils

import subprocess
import logging
import re
import time

logger = logging.getLogger("probe")


class Probe(thread.Thread):
    def __init__(self, target, name=None):
        thread.Thread.__init__(self)
        self.target = target
        self.name = "%s-%s" % (self._probe_name.lower(), utils.sanitize(target))
        if not name:
            name = target
        self.title = "%s %s" % (self._probe_name, name)
        self._throttle_limit = 1.0
        self._throttle_time = 1

    def graphs(self):
        return [self.name]

