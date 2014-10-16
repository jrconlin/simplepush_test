#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import websocket

from pushtest.pushTestCase import PushTestCase
from pushtest.utils import get_uaid


class TestPushAPI(PushTestCase):
    """ General API tests """
    def setUp(self):
        if self.debug:
            websocket.enableTrace(False)
        self.ws = websocket.create_connection(self.url)

    def test_key_case(self):
        test_chid = get_uaid("key_case")
        """ Test key case sensitivity """
        self.ws = websocket.create_connection(self.url)
        ret = self.msg(self.ws, {"messagetype": "hello",
                       "channelIDs": [test_chid],
                       "uaid": get_uaid("CASE_UAID")})
        self.compare_dict(ret, {"status": 401,
                          "error": "Invalid Command"})
        self.msg(self.ws, {"messageType": "purge"})
        self.ws.close()

        # leading trailing spaces
        self.ws = websocket.create_connection(self.url)
        ret = self.msg(self.ws, {" messageType ": "hello",
                       "channelIDs": [test_chid],
                       "uaid": get_uaid("CASE_UAID")})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})
        self.msg(self.ws, {"messageType": "purge"})
        self.ws.close()

        # Cap channelIds
        self.ws = websocket.create_connection(self.url)
        ret = self.msg(self.ws, {"messageType": "hello",
                       "ChannelIds": [test_chid],
                       "uaid": get_uaid("CASE_UAID")})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})
        self.msg(self.ws, {"messageType": "purge"})
        self.ws.close()

        # all cap hello
        self.ws = websocket.create_connection(self.url)
        ret = self.msg(self.ws, {"messageType": "HELLO",
                       "channelIDs": ["test_chid"],
                       "uaid": get_uaid("CASE_UAID")})
        self.compare_dict(ret, {'status': 200, "messageType": "hello"})
        self.msg(self.ws, {"messageType": "purge"})
        self.ws.close()

        # bad register case
        self.ws = websocket.create_connection(self.url)
        uaid = get_uaid("CASE_UAID")
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [test_chid],
                 "uaid": get_uaid("CASE_UAID")})
        ret = self.msg(self.ws, {"messageType": "registeR",
                       "channelIDs": [test_chid],
                       "uaiD": uaid})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})

        # test ack
        self.msg(self.ws, {"messageType": "acK",
                 "channelIDs": [test_chid],
                 "uaid": uaid})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})

        # test ping
        self.msg(self.ws, {"messageType": "PING",
                 "channelIDs": [test_chid],
                 "uaid": uaid})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})
        self.msg(self.ws, {"messageType": "purge"})

    def test_empty_args(self):
        uaid = get_uaid("empty_uaid")
        test_chid = get_uaid("")
        ret = self.msg(self.ws, {"messageType": "",
                       "channelIDs": [test_chid],
                       "uaid": uaid})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})
        self.msg(self.ws, {"messageType": "purge"})

        # Test that an empty UAID after "hello" returns the same UAID
        tmp_uaid = get_uaid("empty_uaid")
        self.ws = websocket.create_connection(self.url)
        ret = self.msg(self.ws, {"messageType": "hello",
                       "channelIDs": [],
                       "uaid": tmp_uaid})
        self.compare_dict(ret, {"status": 200, "messageType": "hello"})

        ret = self.msg(self.ws, {"messageType": "hello",
                       "channelIDs": [],
                       "uaid": ""})
        self.compare_dict(ret, {'status': 200,
                          "uaid": tmp_uaid,
                          "messageType": "hello"})
        self.msg(self.ws, {"messageType": "purge"})
        self.ws.close()
        self.ws = websocket.create_connection(self.url)

        #register (clearing the channel first in case it's already present)
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [],
                 "uaid": uaid})

        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": test_chid,
                       "uaid": ""})
        self.compare_dict(ret, {'status': 200, 'messageType': 'register'})
        self.validate_endpoint(ret['pushEndpoint'])

        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": "",
                       "uaid": uaid})
        self.compare_dict(ret, {"status": 401,
                          "messageType": "register",
                          "error": "Invalid Command"})
        self.msg(self.ws, {"messageType": "purge"})
        # test ping
        # XXX Bug - ping after error isn't updated in response
        # self.msg(self.ws, {"messageType": "ping"})
        # self.compare_dict(ret, {'status': 200, 'messageType': 'ping'})

    def test_chan_limits(self):
        """ Test string limits for keys """
        import pdb; pdb.set_trace()
        uaid = get_uaid("chan_limit_uaid")
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [get_uaid("chan_limits")],
                 "uaid": uaid})
        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": "%s" % self.chan_150[:101]})
        self.compare_dict(ret, {"status": 401,
                          "messageType": "register",
                          "error": "Invalid Command"})

        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": "%s" % self.chan_150[:100]})
        self.compare_dict(ret, {"status": 200, "messageType": "register"})
        self.validate_endpoint(ret['pushEndpoint'])

        # hello 100 channels
        ret = self.msg(self.ws, {"messageType": "hello",
                       "channelIDs": self.big_uuid,
                       "uaid": uaid})
        self.compare_dict(ret, {"status": 503, "messageType": "hello"})

        # register 100 channels
        for chan in self.big_uuid:
            ret = self.msg(self.ws, {"messageType": "register",
                           "channelID": chan,
                           "uaid": uaid})
            self.compare_dict(ret, {"status": 200, "messageType": "register"})
            self.validate_endpoint(ret['pushEndpoint'])

    def tearDown(self):
        self.msg(self.ws, {"messageType": "purge"})
        self.ws.close()

if __name__ == '__main__':
    unittest.main(verbosity=2)
