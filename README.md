**Welcome to the project set_up_game thing.**

CA/Team 5: Filip Matracki, Ksawery Jasieński, Tomek Marcińczyk, Fardin Mohammed

*Running the server:*

>python server.py

Possible parameters: 

* -v (--verbose) start the server in verbose mode (print out all debugging information)

After starting the server, it will wait for and handle client connections. It is possible to interact with the server via console commands:

* echo [message] : echo back the message
* state|status : print how many clients are currently connected
* clients : print details about each of the connected clients
* toggle-verbose : switch verbose mode on/off
* quit|close|exit|stop : shut down the server

*Running the clients:*
>python player.py

Possible parameters: 
* -c (--playercount) specifies the number of clients to run (default is 1)
* -v (--verbose) runs the client in verbose mode

        After running, the script deploys the specified number of clients.