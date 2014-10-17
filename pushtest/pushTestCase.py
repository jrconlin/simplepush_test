
import ConfigParser
import json
import unittest
import socket
from utils import (str_gen, str2bool, log as print_log, compare_dict as comp_dict, read_config)


class PushTestCase(unittest.TestCase):
    """ General API tests """
    config = read_config('../config.ini')
    url = config.get('server', 'url')
    debug = str2bool(config.get('debug', 'trace'))
    verbose = str2bool(config.get('debug', 'verbose'))

    ## Note: The protocol notes that a re-registration with the same
    #  channel number should return a 409. This can cause problems
    #  for large servers, since it requires the server to maintain
    #  states for each uaid+channel pair. These tests are commented
    #  out until we can either detect the type of server we're running
    #  against, or otherwise resolve the issue.
    allow_dupes = str2bool(config.get('server', 'allow_dupes'))

    # JSON object keys are case-sensitive by default; however, Go's JSON
    # decoder accepts case-insensitive matches. This is a PushGo-specific
    # behavior that is not guaranteed across implementations.
    case_sensitive_keys = str2bool(config.get('server', 'case_sensitive_keys'))

    # data types
    uuid = ['f7067d44-5893-407c-8d4c-fc8f7ed97041',
            '0cb8a613-8e2b-4b47-b370-51098daa8401']

    invalid_uuid = ['1c57e340-df59-44648105-b91f1a39608b',
                    '14a84c48-2b8c-4669-8976--541368ccf4d3']

    big_uuid = uuid * 100

    strings = {
        'valid_uaid': {'status': 503},
        ' fooey barrey ': {'status': 503},
        '!@#$%^&*()-+': {'status': 503},
        '0': {'status': 503},
        '1': {'status': 503},
        '-66000': {'status': 503},
        uuid[0]: {'status': 200, 'uaid': uuid[0]},
        invalid_uuid[1]: {'status': 503},
        'True': {'status': 503},
        'False': {'status': 503},
        'true': {'status': 503},
        'false': {'status': 503},
        '\"foo bar\"': {'status': 503},
        str_gen(64000): {'status': 503}
    }
    data_types = ['messageType', 'HeLLO', '!@#$%^&*()-+', '0',
                  '1', '-66000', '', uuid[1],
                  1, 0, -1, True, False, None, ' fooey barrey ',
                  str_gen(64000), chr(0), '\x01\x00\x12\x59']

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def log(self, prefix, msg=""):
        if self.verbose:
            print_log(prefix, msg)

    def close(self, ws):
        try:
            ws.send('{"messageType": "purge"}')
        except socket.error, e:
            # If the server closed the connection, e[0] == errno.EPIPE.
            pass
        finally:
            ws.close()

    def msg(self, ws, msg, cb='cb'):
        """ Util that sends and returns dict"""
        self.log("SEND:", msg)
        try:
            ws.send(json.dumps(msg))
        except Exception as e:
            print 'Unable to send data', e
            return None
        if cb:
            try:
                ret = ws.recv()
                if ret is None or len(ret) == 0:
                    return None
                return json.loads(ret)
            except Exception, e:
                print '#### Unable to parse json:', e
                raise AssertionError(e)

    def compare_dict(self, ret_data, exp_data, exit_on_assert=False):
        """ compares two dictionaries and raises assert with info """
        self.log("RESPONSE GOT:", ret_data)
        self.log("RESPONSE EXPECTED:", exp_data)

        diff = comp_dict(ret_data, exp_data)

        if diff["errors"]:
            print 'AssertionError', diff["errors"]
            if exit_on_assert:
                exit("AssertionError: %s" % diff["errors"])
            raise AssertionError(diff["errors"])
        return True

    def validate_endpoint(self, endpoint):
        """ validate endpoint is in proper url format """
        self.assertRegexpMatches(endpoint, r'(http|https)://.*/update/.*')
