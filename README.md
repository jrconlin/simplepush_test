# NOTE

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
This package is considered ***OBSOLETE***  and is no longer supported
or maintained.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


This is a simple test harness for the pushgo server.

This test harness is designed to exercise the server functions.

## Server API Testing
Run `make` to install dependencies.

You can run the complete smoke tests invoking
`PUSH_SERVER=wss://WEBSOCKETHOST/ make test`. These tests exercise basic
delivery and uaid reconnect resumption behavior along with storage of
notifications while disconnected.

To run the tests not requiring storage, invoke:
`PUSH_SERVER=wss://WEBSOCKETHOST/ ./bin/nosetests test_loop`.

You can also run acceptance level tests by invoking `./run_all.py`. You
can run a specific test file by passing the filename as an argument.
Debug output is controlled by config.ini.

## Docker

To run the tests in a Docker container, execute the following command,
replacing `ws://localhost:8080` with the Simple Push server URI:

    docker run -e TEST_URL=ws://localhost:8080 kitcambridge/simplepush_test:latest
