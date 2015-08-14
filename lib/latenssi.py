#!/usr/bin/env python
# encoding: utf-8


from lib import rrd, config, probe, web, probes

import os
import time

import settings


def load_settings():
    setting_vars = vars(settings)
    config.load_config(setting_vars)

load_settings()

from lib.routes import *

from time import sleep

import logging
logger = logging.getLogger("Latenssi")

settings_imported = time.time()

probe.populate()


def settings_changed():
    global settings_imported
    settings_file = settings.__file__
    if settings_file.endswith('.pyc'):
        settings_file = settings_file[:-1]
    modification_time = os.path.getmtime(settings_file)
    if modification_time > settings_imported:
        logger.warn("Settings changes")
        try:
            reload(settings)
        except SyntaxError:
            logger.exception("Settings file have an syntax error")
            return False
        load_settings()
        settings_imported = modification_time
        return True
    return False


def graph():
    """
    Generate static graphs
    """
    for interval_name, interval in config.intervals.items():
        for child in probe.probes:
            for graph in child.graphs():
                rrd.RRD.graph(graph, interval=interval_name)


def html():
    """
    Generate html files
    """
    web.generate_pages()

def webdaemon():
    web.webapp.run(host=config.bind_address, port=config.bind_port, reloader=config.devel)

def daemon():
    childs = []
    for p in probe.probes:
        childs.append(p)

    childs.append(rrd.RRD)

    for child in childs:
        child.start()

    try:
        while True:
            sleep(10)
            if settings_changed():
                probe.populate(reload=True)
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        logger.exception("Unhandled exception")


    for child in childs:
        try:
            child.stop()
        except Exception as e:
            logger.error("Cannot stop child")
            logger.exception(e)
