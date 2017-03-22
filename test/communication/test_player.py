#!/usr/bin/env python

import pytest
from src.communication import player, server


class PlayerTest:
    def __init__(self):
        self.guinea_player = player
        self.guinea_server = server

    def test_unit(self):
        assert self.guinea_player.run() == 1

    def test_integration(self):
        assert self.guinea_server.run() == 1


