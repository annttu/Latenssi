# encoding: utf-8

import os
import time

import settings
import logging
from lib import thread, probe
from lib import config as config_object

_reload = reload

logger = logging.getLogger("config_utils")


def poll_settings_changed():
    settings_file = settings.__file__
    if settings_file.endswith('.pyc'):
        settings_file = settings_file[:-1]
    modification_time = os.path.getmtime(settings_file)
    if modification_time > config_object.last_updated:
        logger.warn("Settings changes")
        load_config(reload=True)
        config_object.last_updated = modification_time
        return True
    return False


def load_config(reload=False):
    if reload:
        try:
            logger.warn("Reloading configuration")
            _reload(settings)
        except SyntaxError:
            logger.exception("Settings file have an syntax error")
            return False
    config = vars(settings)
    for k, v in config.items():
        if k.startswith('_'):
            continue
        if reload:
            if k not in ['probes', 'hosts']:
                continue
        setattr(config_object, k, v)


class ConfigReloader(thread.Thread):

    def __init__(self, start_pollers=True):
        thread.Thread.__init__(self)
        self.start_pollers = start_pollers
        logger.info("Starting config reloader!")

    def main(self):
        if poll_settings_changed():
            probe.populate(reload=True, autostart=self.start_pollers)
        time.sleep(10)

