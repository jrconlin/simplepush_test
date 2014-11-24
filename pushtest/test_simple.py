import os

from nose.tools import eq_, ok_

from pushtest.client import (
    Client,
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
    client.send_notification()
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
    client.send_notification()
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


def test_dont_deliver_acked(url=None):
    url = url or check_environ()
    client = quick_register(url)
    client.disconnect()
    ok_(client.channels)
    chan = client.channels.keys()[0]
    client.send_notification()
    client.connect()
    client.hello()
    result = client.get_notification()
    update = result["updates"][0]
    eq_(update["channelID"], chan)
    client.ack(chan, update["version"])
    client.disconnect()
    client.connect()
    client.hello()
    result = client.get_notification()
    eq_(result, {})


def test_no_delivery_to_unregistered(url=None):
    url = url or check_environ()
    client = quick_register(url)
    client.disconnect()
    ok_(client.channels)
    chan = client.channels.keys()[0]
    client.send_notification()
    client.connect()
    client.hello()
    result = client.get_notification()
    eq_(result["updates"][0]["channelID"], chan)

    client.unregister(chan)
    client.disconnect()
    client.connect()
    client.hello()
    result = client.get_notification()
    eq_(result, {})
