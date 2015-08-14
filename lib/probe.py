# encoding: utf-8

from lib import config, exceptions
import logging

logger = logging.getLogger("Probe")

probe_types = {}

probes = []
probes_dict = {}

probe_cache = {}

def create_probe(host, probe, options, start=False):
    """
    Initialize probe class
    host = hostname
    name = probe name
    """
    if probe not in probe_cache:
        if probe not in config.probes:
            raise exceptions.ConfigError("No probe named %s" % probe)
        if 'type' not in config.probes[probe]:
            raise exceptions.ConfigError("Error parsing probe %s, type is mandatory variable for probe" % probe)
        if config.probes[probe]['type'] not in probe_types:
            raise exceptions.ConfigError("Invalid probe type %s" % config.probes[probe]['type'])
        opts = {}
        for k,v in config.probes[probe].items():
            if k not in ['type']:
                opts[k] = v
        # Create anonymous wrapper for probe
        probe_cache[probe] = lambda x, y: probe_types[config.probes[probe]['type']](x, name=y, **opts)
    if 'name' in options:
        name = options['name']
    else:
        name = host
    p = probe_cache[probe](host, name)
    if p.name not in probes_dict:
        logger.info("Adding new probe %s" % p.name)
        probes.append(p)
        probes_dict[p.name] = p
        if start:
            p.start()
    else:
        logger.info("Skipping already added probe %s" % p.name)
    return p


def populate(reload=False):
    """
    Initialize configured probes
    """
    global probe_cache
    if probes and not reload:
        # Populate only once
        return
    elif reload:
        logger.info("Adding missing probes...")
        probe_cache = {}
    probe_threads = []
    for hostname, host in config.hosts.items():
        for p in host['probes']:
            probe_thread = create_probe(hostname, p, host, start=reload)
            probe_threads.append(probe_thread.name)
    if reload:
        logger.info("Removing missing probes...")
        for probe in probes:
            if probe.name not in probe_threads:
                logger.info("Stopping removed probe %s" % probe.name)
                probe.stop()
                del probes_dict[probe.name]
                i = probes.index(probe)
                del probes[i]


def register_probe(name, module):
    if name not in probe_types:
        probe_types[name] = module

