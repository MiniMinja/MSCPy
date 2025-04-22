import communicationProcess

import time
import threading
import signal
import sys

from fastapi import FastAPI
from typing import Annotated

app = FastAPI()

TIMEOUT = 5

def receive_server(signalNumber, frame):
    print("Received: ", signalNumber)
    sys.exit()

@app.on_event("startup")
async def startup_event():
    communicationProcess.startProcess()
    signal.signal(signal.SIGINT, receive_server)

def makeResponse(room="SYS", res="SYSTEM ERROR"):
    return {"room": room, "res": res}

def processQuery(ID, msg):
    communicationProcess.addRequest(ID, msg)
    queryRes = 'Response timed out'
    time_start = time.time()
    while True:
        if communicationProcess.responseAvailable(ID):
            queryRes = communicationProcess.popResponse(ID)
            break
        print("Time elapsed processing: {}".format(time.time() - time_start))
        if time.time()  - time_start > TIMEOUT:
            break
    if queryRes == "SUCCESS":
        communicationProcess.__processQueue.display()
    return queryRes


@app.get("/")
async def root():
    return makeResponse()

@app.get("/create/")
async def create(
    r : Annotated[str, "name of room"]
):
    uniqueID = communicationProcess.getUniqueID()
    msg = 'create::{}'.format(r)

    queryRes = processQuery(uniqueID, msg)
    
    return makeResponse(res = queryRes)

@app.get("/broadcast/")
async def broadcast(
    r : Annotated[str, "name of room"], 
    res : Annotated[str, "message to broadcast"]
):
    uniqueID = communicationProcess.getUniqueID()
    msg = 'broadcast::{}::{}'.format(r, res)

    queryRes = processQuery(uniqueID, msg)
    
    return makeResponse(res = queryRes)
    
@app.get("/read/")
async def read(
    r : Annotated[str, "name of room"] 
):
    uniqueID = communicationProcess.getUniqueID()
    msg = 'read::{}'.format(r)

    queryRes = processQuery(uniqueID, msg)
    
    return makeResponse(res = queryRes)

@app.get("/close/")
async def close(
    r : Annotated[str, "name of room"] 
):
    uniqueID = communicationProcess.getUniqueID()
    msg = 'close::{}'.format(r)

    queryRes = processQuery(uniqueID, msg)
    
    return makeResponse(res = queryRes)
