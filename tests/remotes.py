#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase, main
from lib.remote import RemoteClient, RemoteServer
from lib import config
import time

import logging
logging.basicConfig()
logging.getLogger("").setLevel(logging.DEBUG)

class TestRemoteServer(RemoteServer):
    def __init__(self):
        super(TestRemoteServer, self).__init__()
        self._messages_ = []

    def handler(self, probe, subprobe, value):
        self._messages_.append([probe,subprobe, value])

class TestRemotesBasic(TestCase):
    def setUp(self):
        config.server_address = "127.0.0.1:51515"
        config.bind_address ="127.0.0.1:51515"
        self.server = TestRemoteServer()
        self.server.start()
        time.sleep(1)
        self.client = RemoteClient()
        self.client.start()

    def tearDown(self):
        self.server.stop()
        self.client.stop()

    def test_message_sent(self):
        self.client.send("ping", "pong", 2.01)
        found = False
        for i in range(100):
            time.sleep(0.05)
            if not self.server._messages_:
                continue
            msg = self.server._messages_.pop()
            self.assertEqual(msg[0], 'ping', "Message probe should be ping not %s" % msg[0])
            self.assertEqual(msg[1], 'pong', "Message subprobe should be pong not %s" % msg[1])
            self.assertTrue(msg[2] > 2.0 and msg[2] < 2.02, "Message value is wrong")
            found = True
        if not found:
            self.fail("Cannot get message")


if __name__ == '__main__':
    main()
