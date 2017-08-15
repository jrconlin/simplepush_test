import websocket

import json

import httplib
import urlparse
import pprint
import sys

from pushtest.utils import read_config

chid = "deadbeef-0000-0000-0000-000000000000"
uaid = "decafbad-0000-0000-0000-000000000000"
version = ""
success = False


def on_close(ws):
    print "## Closed"
    if "fail" in ws.state:
        ws.state = ws.state + "_success"
        state_machine(ws)


def on_error(ws, error):
    print "## Error:: " + str(error)
    exit()


def on_message(ws, message):
    print "<<< Recv'd:: " + ws.state + ">> " + message
    if "fail" in ws.state:
        ws.reply = message
        return
    msg = json.loads(message)
    print "<<< " + pprint.pformat(msg)
    type = msg.get("messageType")
    if type is None:
        exit("Unknown message type sent")
    if msg.get("status") is not None:
        ## We have a status element, this is a response field.
        if msg.get("status") != 200:
            ## Normally 200 is success, but because of testing, the channel
            ## may already exist. If so, unregister it and try again.
            if ws.state == 'register':
                ## The test channel is already registered. Clear it and
                ## try again.
                ws.state = "helloagain"
                send_unreg(ws)
                return
    else:
        if type == "notification":
            if ws.state == "update":
                check_update(msg, ws)
                print "### Update pass, shutting down...."
                ## disable this if you want to test multiple messages.
                ws.state = "shutdown"
                send_unreg(ws)
            send_ack(ws, msg)
            return
    if ws.state == "helloagain":
        # retry the registration
        ws.state = "register"
        ws.send(json.dumps({"messageType": ws.state, "channelID": ws.chid}))
        return
    if ws.state == "hello":
        ## We're recognized, try to register the chid channel.
        ## NOTE: Normally, channelIDs are UUID4 type values.
        check_hello(msg)
        ws.state = "register"
        ws.send(json.dumps({"messageType": ws.state, "channelID": ws.chid}))
        return
    if ws.state == "register":
        ## Endpoint is registered. Send an update via the REST interface.
        check_register(msg)
        ws.update_url = msg.get("pushEndpoint")
        ## Look for an Update.
        ws.state = "update"
        send_rest_alert(ws)
        return
    if ws.state == "shutdown":
        print "### SUCCESS!!! Exiting..."
        ws.success = True
        ws.close()


def on_open(ws):
    print ws.state
    state_machine(ws)


def fail_invalid_string(ws):
    ws.send("banana")


def fail_bad_data_1(ws):
    ws.send(json.dumps({"messageType": 1}))


def fail_bad_data_2(ws):
    ws.send(json.dumps({"messageType": "banana"}))


def state_machine(ws):
    # bad states:
    if False:
        if ws.state == "initialize":
            # do bad states.
            ws.state = "fail_is"
            fail_invalid_string(ws)
            return
        if ws.state == "fail_is_success":
            ws.state = "fail_bdata1"
            fail_bad_data_1(ws)
            return
        if ws.state == "fail_bad_data_1_success":
            ws.state = "fail_bad_data_2"
            fail_bad_data_2(ws)
            return
        if "fail" in ws.state:
            print "!!! Untrapped failure occurred"
            exit(0)
    # do successful
    ws.state = "hello"
    print ">>> Sending 'Hello'"
    ws.send(json.dumps({"messageType": ws.state,
            "uaid": uaid, "channelIDs": []}))


def check_hello(msg):
    try:
        assert "uaid" in msg
        uaid == msg['uaid']
    except AssertionError, e:
        print e
        exit("Hello failed check")
    return


def check_update(msg, ws):
    try:
        assert msg.get("updates")[0].get("channelID") == ws.chid
        if len(ws.version):
            assert msg.get("updates")[0].get("version") == ws.version
    except AssertionError, e:
        print e
        exit("Update failed check")
    return


def check_register(msg):
    try:
        assert msg.get("pushEndpoint") is not None
        assert msg.get("channelID") is not None
    except AssertionError, e:
        print e
        exit("Register Failed")
    return


def send_rest_alert(ws):
    print ">>> Sending REST update"
    url = urlparse.urlparse(ws.update_url)
    http = None
    if url.scheme == "https":
        http = httplib.HTTPSConnection(url.netloc)
    else:
        http = httplib.HTTPConnection(url.netloc)
    http.set_debuglevel(10)
    http.request("PUT", url.path, "version=" + version)
    print "#>> "
    resp = http.getresponse()
    if resp.status != 200:
        exit("invalid url")
    print "#<< " + pprint.pformat(resp.read())


def send_unreg(ws):
    print ">>> Sending Unreg"
    ws.send(json.dumps({"messageType": "unregister", "channelID": chid}))


def send_ack(ws, msg):
    msg['messageType'] = "ack"
    print ">>> send ack" + json.dumps(msg)
    ws.send(json.dumps(msg))


def main():
    config = read_config('config.ini')

    url = config.get('server', 'url')

    websocket.enableTrace(config.get('debug', 'trace'))

    ws = websocket.WebSocketApp(url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.state = "initialize"
    ws.chid = chid
    ws.version = version
    ws.success = False
    ws.run_forever()
    print("leaving")
    print "=============="
    result = True
    if ws.success:
        print "Smoke test was successful"
    else:
        print "Smoke test failed."
        result = False;
    print "=============="

    if not result:
        sys.exit(-1)

main()
