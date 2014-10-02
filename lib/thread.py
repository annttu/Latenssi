#!/usr/bin/env python
# encoding: utf-8


from lib import config

import threading
import logging
import time

logger = logging.getLogger("Thread")

class Thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop = False
        if '_name' not in vars(self):
            self._name = self.__class__.__name__
        self.name = self._name
        self._throttle_limit = 0.1
        self._throttle_time = 1

    def stop(self):
        """
        Stop thread
        """
        self._stop = True
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
        logger.info("Starting thread %s" % self._name)
        while not self._stop:
            start = time.time()
            try:
                self.main()
            except Exception as e:
                logger.exception(e)
                logger.error("Error occured on thread %s, suspended for 5 seconds" % self.name)
                time.sleep(5)
                continue
            # Busyloop quard
            if (time.time() - start) < self._throttle_limit:
                logger.error("thread %s main loop finished too fast, throttling" % self.name)
                time.sleep(self._throttle_time)
                continue


