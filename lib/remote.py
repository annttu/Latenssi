# encoding: utf-8

"""
Add remote probe support.

This support is only partial and miss many important features as:
* encryption
* support for different probes on client and server

"""

from lib.thread import Thread
from lib import config
import zmq

import logging
import time

logger = logging.getLogger("RemoteHandler")

class RemoteServer(Thread):
    """
    This class is used if Latenssi operates as server

    TODO: check that listen_address is configured
    """
    def __init__(self):

        super(RemoteServer, self).__init__()
        self._name = "RemoteServer"
        self._connect()

    def _connect(self):
        self.context = zmq.Context()
        #self.server = self.context.socket(zmq.REP)
        self.server = self.context.socket(zmq.ROUTER)
        self.server.identity = config.listen_address
        self.server.bind("tcp://%s" % (config.listen_address,))

    def handler(self, probe, subprobe, value):
        """
        Process incoming messages

        :param probe: probe name string
        :param subprobe: subprobe name string
        :param value: float value
        :return: None
        """
        # null handler
        return

    def main(self):
        """
        Hander for incoming messages
        """
        while not self._stop:
            try:
                request = self.server.recv_multipart()
            except Exception as e:
                logger.exception("Unhandled exception")
                break # Interrupted
            print(request)
            address, control = request[:2]
            msg = request[2]
            logger.debug("Got message '%s' from %s" % (msg, address,))
            try:
                (sequence,probe,subprobe,value) = msg.split('|',3)
                value = float(value)
                self.handler(probe, subprobe, value)
            except ValueError:
                logger.error("Got invalid message from client %s" % (address,))
                continue
            self.server.send_multipart((address, control, "%s" % sequence))


class RemoteClient(Thread):
    """
    This class is used if Latenssi operates as client

    TODO: check that server_address is configured
    """

    def __init__(self):
        super(RemoteClient, self).__init__()
        self._messages = []
        self._name = "RemoteClient"
        self.context = None
        self.ctx = None
        self.client = None
        self.poller = None
        self._connect()


    def send(self, probe, subprobe, value):
        if not probe or not subprobe or value is None:
            logger.error("Got invalid data for send()")
            return
        self._messages.insert(0, "%s|%s|%.5f" % (probe, subprobe, float(value)))

    def _connect(self):
        if not self.context:
            self.context = zmq.Context()
        if not self.ctx:
            self.ctx = zmq.Context()
        self.client = self.ctx.socket(zmq.REQ)
        self.client.connect("tcp://%s" % config.server_address)
        if not self.poller:
            self.poller = zmq.Poller()
        self.poller.register(self.client, zmq.POLLIN)

    def _disconnect(self):
        self.poller.unregister(self.client)
        self.client.close()

    def main(self):
        sequence = 0
        while not self._stop:
            if not self._messages:
                time.sleep(1)
                continue
            msg = self._messages.pop()
            logger.debug("Sending message %s with sequence %s" % (msg, sequence))
            self.client.send_string("%d|%s" % (sequence, msg))
            expect_reply = True
            while expect_reply and not self._stop:
                socks = dict(self.poller.poll(config.reply_timeout))
                if socks.get(self.client) == zmq.POLLIN:
                    reply = self.client.recv_string()
                    if int(reply) == sequence:
                        logger.debug("Server replied OK (%s)" % reply)
                        expect_reply = False
                        sequence += 1
                        time.sleep(1)
                    else:
                        logger.error("Malformed reply from server: %s" % reply)
                else:
                    logger.error("No response from server, giving up")
                    self._messages.insert(0, msg)
                    time.sleep(1)
                    self._disconnect()
                    self._connect()



