#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import websocket

from pushtest.pushTestCase import PushTestCase
from pushtest.utils import (get_uaid, str_gen)


class TestPushAPI(PushTestCase):
    """ General API tests """
    def setUp(self):
        if self.debug:
            websocket.enableTrace(False)
        self.ws = websocket.create_connection(self.url)

    def test_type_case(self):
        """ Test message type field name case sensitivity """
        uaid = get_uaid()
        chan_id = get_uaid()
        ret = self.msg(self.ws, {"messagetype": "hello",
                       "channelIDs": [chan_id],
                       "uaid": uaid})

        if self.case_sensitive_keys:
            self.compare_dict(ret, {"status": 401,
                              "error": "Invalid Command"})
        else:
            self.compare_dict(ret, {"messageType": "hello",
                              "status": 200})

    def test_chans_case(self):
        """ Test channel IDs field name case sensitivity """
        uaid = get_uaid()
        ret = self.msg(self.ws, {"messageType": "hello",
                       "ChannelIds": ["CASE_UAID"],
                       "uaid": uaid})

        if self.case_sensitive_keys:
            self.compare_dict(ret, {"status": 401,
                              "error": "Invalid Command"})
        else:
            self.compare_dict(ret, {"messageType": "hello",
                              "status": 200})

    def test_key_whitespace(self):
        """ Test leading and trailing whitespace in key name """
        uaid = get_uaid()
        chan_id = get_uaid()
        ret = self.msg(self.ws, {" messageType ": "hello",
                       "channelIDs": [chan_id],
                       "uaid": uaid})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})

    def test_uppercase_type(self):
        """ Test uppercase handshake message type """
        uaid = get_uaid()
        chan_id = get_uaid()
        ret = self.msg(self.ws, {"messageType": "HELLO",
                       "channelIDs": [chan_id],
                       "uaid": uaid})
        self.compare_dict(ret, {'status': 200, "messageType": "hello"})

    def test_invalid_reg(self):
        """ Test invalid registration request """
        uaid = get_uaid()
        chan_id = get_uaid()
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [chan_id],
                 "uaid": uaid})
        ret = self.msg(self.ws, {"messageType": "registeR",
                       "channelIDs": [chan_id],
                       "uaiD": uaid})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})

    def test_case_ack(self):
        """ Test ack without handshake """
        uaid = get_uaid()
        chan_id = get_uaid()
        ret = self.msg(self.ws, {"messageType": "acK",
                       "channelIDs": [chan_id],
                       "uaid": uaid})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})

    def test_case_ping(self):
        """ Test uppercase ping message type """
        uaid = get_uaid()
        chan_id = get_uaid()
        ret = self.msg(self.ws, {"messageType": "PING",
                       "channelIDs": [chan_id],
                       "uaid": uaid})
        if ret != {}:
            self.compare_dict(ret, {"messageType": "ping",
                "status": 200})

    def test_missing_type(self):
        """ Test missing message type """
        uaid = get_uaid()
        chan_id = get_uaid()
        ret = self.msg(self.ws, {"messageType": "",
                       "channelIDs": [chan_id],
                       "uaid": uaid})
        self.compare_dict(ret, {'status': 401, 'error': 'Invalid Command'})

    def test_empty_uaid(self):
        """ Test empty UAID following handshake """
        tmp_uaid = get_uaid()
        ret = self.msg(self.ws, {"messageType": "hello",
                       "channelIDs": [],
                       "uaid": tmp_uaid})
        self.compare_dict(ret, {"status": 200, "messageType": "hello"})

        # Omitting the UAID after the handshake should return the
        # original UAID.
        ret = self.msg(self.ws, {"messageType": "hello",
                       "channelIDs": [],
                       "uaid": ""})
        self.compare_dict(ret, {'status': 200,
                          "uaid": tmp_uaid,
                          "messageType": "hello"})

    def test_empty_chan_id(self):
        """ Test empty channel ID following registration """
        uaid = get_uaid()
        chan_id = get_uaid()
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [],
                 "uaid": uaid})

        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": chan_id,
                       # uaid is an extra field that should be ignored.
                       "uaid": ""})
        self.compare_dict(ret, {'status': 200, 'messageType': 'register'})
        self.validate_endpoint(ret['pushEndpoint'])

        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": "",
                       "uaid": uaid})
        self.compare_dict(ret, {"status": 401,
                          "messageType": "register",
                          "error": "Invalid Command"})
        # test ping
        # XXX Bug - ping after error isn't updated in response
        # self.msg(self.ws, {"messageType": "ping"})
        # self.compare_dict(ret, {'status': 200, 'messageType': 'ping'})

    def test_large_chan_id(self):
        uaid = get_uaid()
        self.msg(self.ws, {"messageType": "hello",
            "channelIDs": [], "uaid": uaid})

        chan_id = str_gen(17)
        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": chan_id})
        self.compare_dict(ret, {"status": 401,
                          "messageType": "register",
                          "error": "Invalid Command"})

    def test_too_many_chans(self):
        """ Test string limits for keys """
        uaid = get_uaid()
        chan_id = get_uaid()
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [chan_id],
                 "uaid": uaid})

        # hello 100 channels
        ret = self.msg(self.ws, {"messageType": "hello",
                       "channelIDs": self.big_uuid,
                       "uaid": uaid})
        self.compare_dict(ret, {"status": 503, "messageType": "hello"})

    def test_reg_all_chans(self):
        uaid = get_uaid()
        chan_id = get_uaid()
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [chan_id],
                 "uaid": uaid})

        # register 100 channels
        for chan in self.big_uuid:
            ret = self.msg(self.ws, {"messageType": "register",
                           "channelID": chan,
                           "uaid": uaid})
            self.compare_dict(ret, {"status": 200, "messageType": "register"})
            self.validate_endpoint(ret['pushEndpoint'])

    def tearDown(self):
        self.close(self.ws)

if __name__ == '__main__':
    unittest.main(verbosity=2)
