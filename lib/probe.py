#!/usr/bin/env python
# encoding: utf-8

"""
Probe template class
"""

from lib import config

from threading import Thread
import subprocess
import logging
import re
import time

# kapsi.fi : xmt/rcv/%loss = 5/5/0%, min/avg/max = 0.00/0.91/1.40

fping_success = re.compile("^(?P<dest>[\w\d:\.-]+) : xmt/rcv/%loss = (?P<xmt>\d+)/(?P<rcv>\d+)/(?P<loss>\d+)%, min/avg/max = (?P<min>\d+.\d\d)/(?P<avg>\d+.\d\d)/(?P<max>\d+.\d\d)$")


logger = logging.getLogger("ping")

class Probe(Thread):
    def __init__(self, target):
        Thread.__init__(self)
        self.target = target
        self._stop = False
        if '_name' not in vars(self):
            self._name = self.__class__.__name__
        self.name = "%s-%s" % (self._name.lower(), target.replace(".", "_"))
        self.title = "%s %s" % (self._name, target)

    def stop(self):
        """
        Stop thread
        """
        self._stop = True
        self.sync(force=True)
        self._kill()


    def _kill(self):
        """
        Kill processes, save state etc
        """
        pass

    def main(self):
        """
        This functions is looped forever,
        add probe functionality to this function
        """
        pass

    def run(self):
        logger.info("Starting probe %s" % self.name)
        while not self._stop:
            start = time.time()
            try:
                self.main()
            except Exception as e:
                logger.exception(e)
                logger.error("Error occured on probe %s, suspended for 5 seconds" % self.name)
                time.sleep(5)
                continue
            # Busyloop quard
            if (time.time() - start) < 1.0:
                logger.error("Probe finished too fast, trottling")
                time.sleep(1)
                continue


