import os
import time
import uuid

from nose.tools import eq_, ok_

from pushtest.client import (
    Client,
    quick_register
)


def check_environ():
    return os.environ.get("PUSH_SERVER")


def test_hello_echo(url=None):
    url = url or check_environ()
    client = Client(url, use_webpush=True)
    client.connect()
    result = client.hello()
    ok_(result != {})
    eq_(result["use_webpush"], True)


def test_basic_delivery(url=None):
    data = str(uuid.uuid4())
    url = url or check_environ()
    client = quick_register(url, use_webpush=True)
    result = client.send_notification(data=data)
    eq_(result["headers"]["encryption"], client._crypto_key)
    eq_(result["data"], data)
    eq_(result["messageType"], "notification")


def test_delivery_repeat_without_ack(url=None):
    data = str(uuid.uuid4())
    url = url or check_environ()
    client = quick_register(url, use_webpush=True)
    client.disconnect()
    ok_(client.channels)
    client.send_notification(data=data, status=202)
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    eq_(result["data"], data)

    client.disconnect()
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    eq_(result["data"], data)


def test_multiple_delivery_repeat_without_ack(url=None):
    data = str(uuid.uuid4())
    data2 = str(uuid.uuid4())
    url = url or check_environ()
    client = quick_register(url, use_webpush=True)
    client.disconnect()
    ok_(client.channels)
    client.send_notification(data=data, status=202)
    client.send_notification(data=data2, status=202)
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    ok_(result["data"] in [data, data2])
    result = client.get_notification()
    ok_(result != {})
    ok_(result["data"] in [data, data2])

    client.disconnect()
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    ok_(result["data"] in [data, data2])
    result = client.get_notification()
    ok_(result != {})
    ok_(result["data"] in [data, data2])


def test_multiple_delivery_with_single_ack(url=None):
    data = str(uuid.uuid4())
    data2 = str(uuid.uuid4())
    url = url or check_environ()
    client = quick_register(url, use_webpush=True)
    client.disconnect()
    ok_(client.channels)
    client.send_notification(data=data, status=202)
    client.send_notification(data=data2, status=202)
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    ok_(result["data"] in [data, data2])
    result = client.get_notification()
    ok_(result != {})
    ok_(result["data"] in [data, data2])
    client.ack(result["channelID"], result["version"])

    client.disconnect()
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    ok_(result["data"] in [data, data2])
    ok_(result["messageType"], "notification")
    result = client.get_notification()
    eq_(result, None)


def test_multiple_delivery_with_multiple_ack(url=None):
    data = str(uuid.uuid4())
    data2 = str(uuid.uuid4())
    url = url or check_environ()
    client = quick_register(url, use_webpush=True)
    client.disconnect()
    ok_(client.channels)
    client.send_notification(data=data, status=202)
    client.send_notification(data=data2, status=202)
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    ok_(result["data"] in [data, data2])
    result2 = client.get_notification()
    ok_(result2 != {})
    ok_(result2["data"] in [data, data2])
    client.ack(result2["channelID"], result2["version"])
    client.ack(result["channelID"], result["version"])

    client.disconnect()
    client.connect()
    client.hello()
    result = client.get_notification()
    eq_(result, None)


def test_no_delivery_to_unregistered(url=None):
    data = str(uuid.uuid4())
    url = url or check_environ()
    client = quick_register(url, use_webpush=True)
    client.disconnect()
    ok_(client.channels)
    chan = client.channels.keys()[0]
    client.send_notification(data=data, status=202)
    client.connect()
    client.hello()
    result = client.get_notification()
    eq_(result["channelID"], chan)
    eq_(result["data"], data)

    client.unregister(chan)
    client.disconnect()
    time.sleep(1)
    client.connect()
    client.hello()
    result = client.get_notification()
    eq_(result, None)
