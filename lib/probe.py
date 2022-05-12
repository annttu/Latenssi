# encoding: utf-8

from lib import config, exceptions, utils
import logging

logger = logging.getLogger("Probe")

single_probe_types = {}
multi_probe_types = {}

probes = []
multi_probes = []
single_probes_dict = {}
multi_probes_dict = {}

single_probe_cache = {}
multi_probe_cache = {}


class PseudoProbe(object):
    def __init__(self, probe, name, target):
        self.name = "%s-%s" % (probe._name.lower(), utils.sanitize(target))
        self.title = "%s %s" % (probe._name, name)
        self.target = target
        self._name = probe._name

    def graphs(self):
        return [self.name]


def create_probe(host, probe, options, start=False):
    if probe in config.multi_probes:
        return create_multi_probe(host, probe, options=options, start=start)
    return create_single_probe(host, probe, options=options, start=start)


def create_single_probe(host, probe, options, start=False):
    """
    Initialize probe class
    host = hostname
    name = probe name
    """
    if probe not in single_probe_cache:
        if probe not in config.probes:
            raise exceptions.ConfigError("No probe named %s" % probe)
        if 'type' not in config.probes[probe]:
            raise exceptions.ConfigError("Error parsing probe %s, type is mandatory variable for probe" % probe)
        if config.probes[probe]['type'] not in single_probe_types:
            raise exceptions.ConfigError("Invalid probe type %s" % config.probes[probe]['type'])
        opts = {}
        for k,v in config.probes[probe].items():
            if k not in ['type']:
                opts[k] = v
        # Create anonymous wrapper for probe
        single_probe_cache[probe] = lambda x, y: single_probe_types[config.probes[probe]['type']](x, name=y, **opts)
    if 'name' in options:
        name = options['name']
    else:
        name = host
    p = single_probe_cache[probe](host, name)
    if p.name not in single_probes_dict:
        logger.warn("Adding new probe %s" % p.name)
        probes.append(p)
        single_probes_dict[p.name] = p
        if start:
            logger.warn("Starting probe %s" % p.name)
            p.start()
    else:
        logger.info("Skipping already added probe %s" % p.name)
    return p.name


def create_multi_probe(host, probe, options, start=False):
    """
    Initialize multi probe class
    host = hostname
    name = probe name
    """
    if probe not in multi_probe_cache:
        if probe not in config.multi_probes:
            raise exceptions.ConfigError("No multiprobe named %s" % probe)
        if 'type' not in config.multi_probes[probe]:
            raise exceptions.ConfigError("Error parsing probe %s, type is mandatory variable for probe" % probe)
        if config.multi_probes[probe]['type'] not in multi_probe_types:
            raise exceptions.ConfigError("Invalid multi probe type %s" % config.multi_probes[probe]['type'])
        opts = {}
        for k, v in config.multi_probes[probe].items():
            if k not in ['type']:
                opts[k] = v
        # Create anonymous wrapper for probe
        multi_probe_cache[probe] = lambda: multi_probe_types[config.multi_probes[probe]['type']](**opts)
    if 'name' in options:
        name = options['name']
    else:
        name = host

    if probe not in multi_probes_dict:
        logger.warn("Adding new multi probe %s" % probe)
        multi_probes_dict[probe] = multi_probe_cache[probe]()
        if start:
            logger.warn("Starting multi probe %s" % probe)
            multi_probes_dict[probe].start()

    multi_probes_dict[probe].add_host(host, name)
    multi_probes.append(PseudoProbe(multi_probes_dict[probe], name, host))
    return name


def populate(reload=False, autostart=False):
    """
    Initialize configured probes
    """
    global single_probe_cache
    global multi_probe_cache
    if probes and not reload:
        # Populate only once
        return
    elif reload:
        logger.info("Adding missing probes...")
        single_probe_cache = {}
        multi_probe_cache = {}
    probe_threads = []
    for hostname, host in config.hosts.items():
        for p in host['probes']:
            probe_name = create_probe(hostname, p, host, start=autostart)
            probe_threads.append(probe_name)
    if reload:
        logger.info("Removing removed probes...")
        to_remove = []
        for probe in probes:
            if probe.name not in probe_threads:
                logger.warn("Stopping removed probe %s" % probe.name)
                if probe.is_alive:
                    try:
                        probe.stop()
                    except Exception:
                        logger.exception("Got unhandled exception while stopping probe")
                to_remove.append(probe)
        for probe in to_remove:
            del single_probes_dict[probe.name]
            i = probes.index(probe)
            del probes[i]


def register_single_probe(name, module):
    if name not in single_probe_types:
        single_probe_types[name] = module


def register_multi_probe(name, module):
    if name not in multi_probe_types:
        multi_probe_types[name] = module
