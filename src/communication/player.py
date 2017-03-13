#!/usr/bin/env python
from socket import *

s = socket()
host = "P21703"
port = 6969


print("fuck off")
s.connect((host,port))
received = s.recv(1024)
print(received.decode())
s.close