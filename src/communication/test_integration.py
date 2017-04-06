#!/usr/bin/env python
from threading import Thread
from time import sleep
from unittest import TestCase

from communication import server, client


class TestIntegration(TestCase):
    def setUp(self):
        sleep(0.5)

        self.mock_client = client.Client(index=0, verbose=True)
        self.mock_server = server.CommunicationServer(verbose=False)

        listening_thread = Thread(target=self.mock_server.listen, daemon=True)
        listening_thread.start()

    def tearDown(self):
        self.mock_server.shutdown()
        self.mock_client.shutdown()

        del self.mock_server
        del self.mock_client

        print()

    def test_echo(self):
        """
        verify that the "echo" functionality of the server works.
        """
        self.mock_client.connect()

        sent = "Message."
        self.mock_client.send(sent)
        received = self.mock_client.receive()

        assert received == ("Your message was: " + sent)

    def test_heavy_load(self):
        """
        test that the mock_client doesn't connect to the server when it's fully occupied
        """
        self.mock_server.clientLimit = 3

        self.mock_client.interConnectionTime = 1
        self.mock_client.connectionAttempts = 3

        simulation = Thread(target=client.simulate, daemon=True, args=(3, False, 5, 1))
        simulation.start()

        sleep(4)

        assert self.mock_client.connect() is False
