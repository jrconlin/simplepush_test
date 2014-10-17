#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest
import websocket
import signal

from pushtest.pushTestCase import PushTestCase
from pushtest.utils import (get_uaid, str_gen, send_http_put, log)


class TestPushAPI(PushTestCase):
    """ General API tests """
    def setUp(self):
        if self.debug:
            websocket.enableTrace(False)
        self.ws = websocket.create_connection(self.url)

    def test_hello_bad_types(self):
        """ Test handshake messageType with lots of data types """
        for dt in self.data_types:
            tmp_uaid = get_uaid()
            verify_json = {"messageType": ("%s" % dt).lower(),
                           "status": 401,
                           "uaid": tmp_uaid}
            ws = websocket.create_connection(self.url)
            try:
                ret = self.msg(ws, {"messageType": ('%s' % dt).lower(),
                               "channelIDs": [],
                               "uaid": tmp_uaid})
                if dt == 'HeLLO':
                    verify_json["status"] = 200
                else:
                    verify_json["error"] = "Invalid Command"
                self.compare_dict(ret, verify_json)
            finally:
                self.close(ws)

    # sending non self.strings to make sure it doesn't break server
    def test_non_string_type(self):
        """ Test non-string message type """
        self.ws.send('{"messageType": 123}')
        self.compare_dict(json.loads(self.ws.recv()), {"status": 401})

    def test_null_type(self):
        """ Test null message type """
        try:
            self.ws.send('{"messageType": null}')
        except Exception, e:
            print 'Exception', e

    def chans_unknown_uaid(self):
        unknown_uaid = str_gen(32)
        ret = self.msg(self.ws, {"messageType": "hello",
            "customKey": "custom value",
            # sending channelIDs with an unknown UAID should trigger
            # a client reset (return a different UAID)
            "channelIDs": ["1", "2"],
            "uaid": unknown_uaid})

        self.compare_dict(ret, {"status": 401})

    def test_hello_uaid_types(self):
        """ Test handshake uaids with lots of data types """
        for string in self.strings:
            print string
            msg = {"messageType": "hello",
                   "customKey": "custom value",
                   "channelIDs": [],
                   "uaid": "%s" % string}

            ws = websocket.create_connection(self.url)
            try:
                ws.send(json.dumps(msg))
                ret = json.loads(ws.recv())
            finally:
                self.close(ws)

            valid_json = self.strings[string]
            self.compare_dict(ret, valid_json)


    def test_hello_invalid_keys(self):
        """ Test various json keys """
        for dt in self.data_types:
            invalid_ws = websocket.create_connection(self.url)
            try:
                invalid_ws.send(json.dumps({"%s" % dt: "hello"}))
                ret = json.loads(invalid_ws.recv())
            except Exception as e:
                print 'Exception - Unable to read socket: ', e
            finally:
                self.close(invalid_ws)

            if dt == 'messageType':
                self.compare_dict(ret, {"messageType": "hello",
                                        "status": 401,
                                        "error": "Invalid Command"})
            else:
                self.compare_dict(ret, {"status": 401,
                                  "error": "Invalid Command"})

    def test_reg_noshake(self):
        """ Test registration without prior handshake """
        # no handshake invalid
        uaid = get_uaid()
        chan_id = get_uaid()
        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": chan_id,
                       "uaid": uaid})
        self.compare_dict(ret, {"messageType": "register",
                          "status": 401,
                          "error": "Invalid Command"})

    def test_reg_handshake(self):
        """ Test registration with prior handshake """
        uaid = get_uaid()
        chan_id = get_uaid()
        ret = self.msg(self.ws, {"messageType": "hello",
                       "channelIDs": [chan_id],
                       "uaid": uaid})
        if self.allow_dupes:
            ret = self.msg(self.ws, {"messageType": "register",
                           "channelID": chan_id})
            self.compare_dict(ret, {"messageType": "register",
                              "status": 200})
            self.validate_endpoint(ret['pushEndpoint'])

    def test_reg_duplicate(self):
        """ Test registration with duplicate channel name """
        uaid = get_uaid()
        chan_id = get_uaid()
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [chan_id],
                 "uaid": uaid})
        if self.allow_dupes:
            ret = self.msg(self.ws, {"messageType": "register",
                           "channelID": chan_id})
            self.compare_dict(ret, {"messageType": "register",
                              "status": 200})
            # duplicate handshake
            ret = self.msg(self.ws, {"messageType": "register",
                           "channelID": chan_id})
            self.compare_dict(ret, {"messageType": "register",
                              "status": 200})

        # passing in list to channelID
        ret = self.msg(self.ws, {"messageType": "register",
                       "channelIDs": [chan_id]})
        self.compare_dict(ret, {"messageType": "register",
                          "status": 401,
                          "error": "Invalid Command"})

    def test_reg_plural(self):
        """ Test registration with a lot of channels and uaids """
        # XXX bug uaid can get overloaded with channels,
        # adding epoch to unique-ify it.
        uaid = get_uaid()
        chan_id = get_uaid()
        if self.allow_dupes:
            self.msg(self.ws, {"messageType": "hello",
                     "channelIDs": [chan_id],
                     "uaid": uaid})
            ret = self.msg(self.ws, {"messageType": "register",
                           "channelID": chan_id,
                           "uaid": uaid})

            self.compare_dict(ret, {"messageType": "register",
                              "status": 200})

            # valid with same channelID
            ret = self.msg(self.ws, {"messageType": "register",
                           "channelID": chan_id})
            self.compare_dict(ret, {"messageType": "register",
                              "status": 200})

        # loop through different channelID values
        for dt in self.data_types:
            ws = websocket.create_connection(self.url)
            uaid = get_uaid()
            self.msg(ws, {"messageType": "hello",
                     "channelIDs": [],
                     "uaid": uaid})

            try:
                ret = self.msg(ws, {"messageType": "register",
                               "channelID": "%s" % dt,
                               "uaid": uaid})
            finally:
                ws.close()

            if 'error' in ret:
                # lots of errors here, lots of gross logic to
                # validate them here
                continue
            self.compare_dict(ret, {"messageType": "register",
                              "status": 200})

    def test_unreg_missing_chan(self):
        # unreg non existent
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [],
                 "uaid": ""})

        ret = self.msg(self.ws, {"messageType": "unregister"})
        self.compare_dict(ret, {"messageType": "unregister",
                          "status": 401,
                          "error": "Invalid Command"})

    def test_unreg_no_handshake(self):
        """ Test deregistration without prior handshake """
        chan_id = get_uaid()
        ret = self.msg(self.ws, {"messageType": "unregister",
                       "channelID": chan_id})
        self.compare_dict(ret, {"messageType": "unregister",
                          "status": 401,
                          "error": "Invalid Command"})

    def test_unreg(self):
        """ Test unregister """
        # setup
        uaid = get_uaid()
        chan_id = get_uaid()
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [chan_id],
                 "uaid": uaid})
        self.msg(self.ws, {"messageType": "register",
                 "channelID": chan_id})

        # unreg
        ret = self.msg(self.ws, {"messageType": "unregister",
                       "channelID": chan_id})
        self.compare_dict(ret, {"messageType": "unregister",
                          "status": 200})

        # check if channel exists
        ret = self.msg(self.ws, {"messageType": "unregister",
                       "channelID": chan_id})
        # XXX No-op on server results in this behavior
        self.compare_dict(ret, {"messageType": "unregister",
                          "status": 200})

    def test_unreg_race(self):
        """ Test Unregister with outstanding unACKed notifications
            https://bugzilla.mozilla.org/show_bug.cgi?id=894193
        """
        class TimeoutError(Exception):
            pass

        def _timeout(signum, frame):
            raise TimeoutError()

        uaid = get_uaid()
        chan_id = get_uaid()
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [],
                 "uaid": uaid})
        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": chan_id})
        send_http_put(ret["pushEndpoint"])
        try:
            # read the update, but don't ACK it.
            self.ws.recv()
            # unregister the channel
            self.msg(self.ws, {"messageType": "unregister",
                               "channelID": chan_id})
            # make sure we don't get any updates.
            # They should be immediate.
            signal.signal(signal.SIGALRM, _timeout)
            signal.alarm(1)
            self.ws.recv()
            raise AssertionError("ACK of unregistered channel data requested")
        except TimeoutError, e:
            pass
        except Exception, e:
            raise AssertionError(e)

    def test_ping_empty(self):
        # happy
        # Ping responses can contain any data.
        # The reference server returns the minimal data set "{}"
        ret = self.msg(self.ws, {})
        if ret != {}:
            self.compare_dict(ret, {"messageType": "ping",
                                    "status": 200})

    def test_ping_explicit(self):
        # happy
        ret = self.msg(self.ws, {'messageType': 'ping'})
        if ret != {}:
            self.compare_dict(ret, {"messageType": "ping",
                              "status": 200})

    def test_ping_extra_args(self):
        # extra args
        uaid = get_uaid()
        chan_id = get_uaid()
        ret = self.msg(self.ws, {'messageType': 'ping',
                       'channelIDs': [chan_id],
                       'uaid': uaid,
                       'nada': ''})
        if ret != {}:
            self.compare_dict(ret, {"messageType": "ping",
                              "status": 200})

    def test_ping(self):
        # send and ack too
        # XXX ack can hang socket
        # ret = self.msg(self.ws, {"messageType": "ack",
        #                 "updates": [{ "channelID": get_uaid("ping_chan_1"),
        #                 "version": 123 }]})
        # self.compare_dict(ret, {"status": 200, "messageType": "ack"})

        # empty braces is a valid ping
        ret = self.msg(self.ws, {})
        if ret != {}:
            self.compare_dict(ret, {"messageType": "ping",
                              "status": 200})

        for ping in range(100):
            ws = websocket.create_connection(self.url)
            try:
                ret = self.msg(ws, {'messageType': 'ping'})
            finally:
                ws.close()

            if ret != {}:
                self.compare_dict(ret, {"messageType": "ping",
                                  "status": 200})

    def test_ping_reg(self):
        # do a register between pings
        uaid = get_uaid()
        chan_id = get_uaid()

        ret = self.msg(self.ws, {})
        if ret != {}:
            self.compare_dict(ret, {"messageType": "ping",
                              "status": 200})

        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [chan_id],
                 "uaid": uaid})
        ret = self.msg(self.ws, {"messageType": "register",
                       "channelID": chan_id})
        self.compare_dict(ret, {"status": 200, "messageType": "register"})

    def test_ack_no_hello(self):
        # no hello
        chan_id = get_uaid()
        ret = self.msg(self.ws, {"messageType": "ack",
                       "updates": [{"channelID": chan_id,
                                    "version": 23}]})
        self.compare_dict(ret, {"error": "Invalid Command",
                          "status": 401, "messageType": "ack"})
        self.assertEqual(ret["updates"][0]["channelID"], chan_id)
        self.assertEqual(ret["updates"][0]["version"], 23)

    def test_ack(self):
        """ Test ack """
        # happy path
        uaid = get_uaid()
        chan_id = get_uaid()
        self.msg(self.ws, {"messageType": "hello",
                 "channelIDs": [chan_id],
                 "uaid": uaid})
        reg = self.msg(self.ws, {"messageType": "register",
                       "channelID": chan_id})
        assert (reg["pushEndpoint"] is not None)

        # send an http PUT request to the endpoint
        send_http_put(reg['pushEndpoint'])

        # this blocks the socket on read
        # print 'RECV', self.ws.recv()
        # hanging socket against AWS
        ret = self.msg(self.ws, {"messageType": "ack",
                       "updates": [{"channelID": chan_id,
                                    "version": 23}]})
        self.compare_dict(ret, {"messageType": "notification"})
        self.assertEqual(ret["updates"][0]["channelID"], chan_id)

    def tearDown(self):
        self.close(self.ws)

if __name__ == '__main__':
    unittest.main(verbosity=2)
