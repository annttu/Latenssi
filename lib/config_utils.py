# encoding: utf-8

import os
import time

#import settings
import yaml
import logging
from lib import thread, probe
from lib import config as config_object
from lib.exceptions import ConfigError

_reload = reload

logger = logging.getLogger("config_utils")

SETTINGS_FILE = "settings.yaml"
SETTINGS_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), "../", SETTINGS_FILE))


def check_config_file(path=None):
    if not path:
        path = SETTINGS_PATH
    if not os.path.isfile(SETTINGS_PATH):
        raise ConfigError("Settings file %s is missing" % SETTINGS_PATH)
    return True


def poll_settings_changed():
    settings_file = SETTINGS_PATH
    #if settings_file.endswith('.pyc'):
    #    settings_file = settings_file[:-1]
    modification_time = os.path.getmtime(settings_file)
    if modification_time > config_object.last_updated:
        logger.warn("Settings changes")
        try:
            load_config(reload=True)
        except ConfigError as err:
            logger.error(err)
        config_object.last_updated = modification_time
        return True
    return False


def load_config(reload=False):
    config = None
    check_config_file()
    try:
        logger.info("Loading configuration")
        stream = file(SETTINGS_PATH, 'r')
        config = yaml.load(stream)
    except yaml.YAMLError as err:
        if hasattr(err, 'problem_mark'):
            mark = err.problem_mark
            raise ConfigError("Settings file %s have an syntax error at line %s character %s" % (
                SETTINGS_FILE, mark.line+1, mark.column+1))
        else:
            raise ConfigError("Failed to parse settings file.")
    if not config:
        raise ConfigError("Config file is empty or contains invalid content")
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

