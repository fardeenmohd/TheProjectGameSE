#!/usr/bin/env python
from socket import *

s = socket()
host = "P21703"
port = 1922

s.connect((host,port))
received = s.recv(1024)
print(received.decode())
message = input()
s.send(message.encode())
received = s.recv(1024)
print(received.decode())

s.close