import os
import time

from nose.tools import eq_, ok_

from pushtest.client import (
    quick_register
)


def check_environ():
    return os.environ.get("PUSH_SERVER")


def test_delivery_while_disconnected(url=None):
    url = url or check_environ()
    client = quick_register(url)
    client.disconnect()
    ok_(client.channels)
    chan = client.channels.keys()[0]
    client.send_notification(status=202)
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    ok_(result["updates"] > 0)
    eq_(result["updates"][0]["channelID"], chan)


def test_delivery_repeat_without_ack(url=None):
    url = url or check_environ()
    client = quick_register(url)
    client.disconnect()
    ok_(client.channels)
    chan = client.channels.keys()[0]
    client.send_notification(status=202)
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    ok_(result["updates"] > 0)
    eq_(result["updates"][0]["channelID"], chan)

    client.disconnect()
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    ok_(result["updates"] > 0)
    eq_(result["updates"][0]["channelID"], chan)


def test_direct_delivery_without_ack(url=None):
    url = url or check_environ()
    client = quick_register(url)
    result = client.send_notification()
    ok_(result != {})
    client.disconnect()
    client.connect()
    client.hello()
    result2 = client.get_notification(timeout=5)
    ok_(result2 != {})
    update1 = result["updates"][0]
    if 'data' in update1:
        del update1["data"]
    update2 = result2["updates"][0]
    eq_(update1, update2)


def test_dont_deliver_acked(url=None):
    url = url or check_environ()
    client = quick_register(url)
    client.disconnect()
    ok_(client.channels)
    chan = client.channels.keys()[0]
    client.send_notification(status=202)
    client.connect()
    client.hello()
    result = client.get_notification()
    update = result["updates"][0]
    eq_(update["channelID"], chan)
    client.ack(chan, update["version"])
    client.disconnect()
    time.sleep(0.2)
    client.connect()
    client.hello()
    result = client.get_notification()
    eq_(result, None)


def test_no_delivery_to_unregistered(url=None):
    url = url or check_environ()
    client = quick_register(url)
    client.disconnect()
    ok_(client.channels)
    chan = client.channels.keys()[0]
    client.send_notification(status=202)
    client.connect()
    client.hello()
    result = client.get_notification()
    eq_(result["updates"][0]["channelID"], chan)

    client.unregister(chan)
    client.disconnect()
    client.connect()
    client.hello()
    result = client.get_notification()
    eq_(result, None)


def test_deliver_version(url=None):
    url = url or check_environ()
    client = quick_register(url)
    result = client.send_notification(version=12)
    ok_(result is not None)
    eq_(result["updates"][0]["version"], 12)


def test_deliver_version_without_header(url=None):
    url = url or check_environ()
    client = quick_register(url)
    result = client.send_notification(version=12, use_header=False)
    ok_(result is not None)
    eq_(result["updates"][0]["version"], 12)
