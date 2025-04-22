# Mins Server Communicator

>"I've been trying to make something that can connect small projects together
and turns out there is already a thing called "Microservices Architecture".
I just wasted 2 months of my life trying to execute something that can 
be done with just RESTful APIs" - _Note from dev_

This project essentially uses RESTful apis to send commands across servers
eliminating the need for a separate file in a database somewhere called
"searchIndex" (which would hold all the commands, or "queries", as a queue
and load them each time the program loaded up or wrote to the 
database everytime someone added a query -> the previous solution to
communicate between programs).

## MAKE SURE YOU USE A VENV
Make sure you use a venv. It's just good practice.

## Python (pip) dependencies

- FastAPI

## Use

Once you have all the dependecies installed using pip, just run 
`fastapi run communicator.py`

The appropriate URLS you can call are 

- `/create/?r=<roomname>`
this will create a room in in the server that you can listen to

- `/broadcast/?r=<roomname>&res=<msg>`
this will send a message to the room in the server

- `/read/?r=<roomname>`
this will read the message that was broadcasted

- `/close/?r=<roomname>`
this will close the room (as if it were finished)