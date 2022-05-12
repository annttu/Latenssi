#!/usr/bin/env python
# encoding: utf-8

"""
Multi Probe template class
"""

from lib import config, thread, utils

import subprocess
import logging
import re
import time

logger = logging.getLogger("probe")


class MultiProbe(thread.Thread):
    def __init__(self):
        thread.Thread.__init__(self)
        self.targets = {}
        self._throttle_limit = 1.0
        self._throttle_time = 1

    def _add_host_local(self, target, name):
        pass

    def add_host(self, target, name=None):
        if not name:
            name = "%s-%s" % (self._name.lower(), utils.sanitize(target))
        self.targets[target] = name
        self._add_host_local(target, name)

    def graphs(self):
        return list(self.targets.values())

