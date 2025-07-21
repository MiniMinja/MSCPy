import communicationProcess

import time
import threading
import signal
import sys
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from pydantic import BaseModel
from typing import Dict, Any, Optional # for the type of BaseModel

app = FastAPI()

origins =[
    'http://localhost:5173',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TIMEOUT = 5

def receive_server(signalNumber, frame):
    print("Received: ", signalNumber)
    sys.exit()

@app.on_event("startup")
async def startup_event():
    communicationProcess.startProcess()
    print("BROADCASTS LAST {} seconds. Make sure your application grabs them while they are hot and ready".format(communicationProcess.BROADCASTDURATION))
    print("RESOLUTIONS LAST {} seconds. Make sure your client reads them while they are hot and ready".format(communicationProcess.RESOLUTIONTIMER))
    signal.signal(signal.SIGINT, receive_server)

def makeResponse(room="SYS", res="ERROR: SYSTEM ERROR"):
    response = {"room": room, "res": res}
    print("response is: {}".format(str(response)[200:]))
    return response

def processQuery(ID, roomname, msg):
    print("Thread Status: {}".format(communicationProcess.__commProcess.is_alive()))
    if not communicationProcess.__commProcess.is_alive():
        return makeResponse(res='ERROR: PROCESS NOT RUNNING')
    print('>>>IN>>{}: {}'.format(ID, str(msg)[200:]))
    communicationProcess.addRequest(ID, roomname, msg)
    queryRes = 'Response timed out'
    time_start = time.time()
    while True:
        if communicationProcess.responseAvailable(ID):
            queryRes = communicationProcess.popResponse(ID)
            break
        print("Time elapsed processing: {}".format(time.time() - time_start))
        if time.time()  - time_start > TIMEOUT:
            break
    print('<<OUT<<', str(queryRes)[200:])
    return queryRes

class ResolutionBody(BaseModel):
    progress: Dict[str, Any] | None = None
    computedResult: Dict[str, Any] | None = None
@app.get("/")
async def root():
    return makeResponse()

@app.post("/room/")
async def create(
    r : Annotated[str, "name of room"]
):
    uniqueID = communicationProcess.getUniqueID()
    msg = 'create::{}'.format(r)

    queryRes = processQuery(uniqueID, r, msg)
    room = queryRes[0]
    resMsg = queryRes[1]
    
    return makeResponse(room = room, res = resMsg)

@app.post("/broadcast/")
async def broadcast(
    r : Annotated[str, "name of room"], 
    res : Annotated[str, "message to broadcast"],
    body: Optional[ResolutionBody] = None  # ← Optional!
):
    uniqueID = communicationProcess.getUniqueID()
    msg = 'broadcast::{}::{}'.format(r, res)
    bodyAsString = ''
    if body:
        print(body)
        bodyAsString = body.json()
        msg += "@body@"
        msg += bodyAsString

        print("<<<<{}>>>>".format(bodyAsString[200:]))

    queryRes = processQuery(uniqueID, r, msg)
    room = queryRes[0]
    resMsg = queryRes[1]
    
    return makeResponse(room = room, res = resMsg)

@app.get("/broadcast/")
async def getBroadcasts(
    r : Annotated[str, "name of room"], 
):
    uniqueID = communicationProcess.getUniqueID()
    msg = 'getbroadcast::{}'.format(r)

    queryRes = processQuery(uniqueID, r, msg)
    room = queryRes[0]
    resMsg = queryRes[1]
    
    return makeResponse(room = room, res = resMsg)

@app.post("/results/")
async def resolve(
    r : Annotated[str, "name of room"],
    ID: Annotated[str, "id of request when broadcasted"],
    res: Annotated[str, "The message you want to send as a resolution to the query"],
    body: ResolutionBody
):
    print("VVVVV")
    print(str(body)[:200])
    print("^^^^")
    uniqueID = communicationProcess.getUniqueID()
    bodyAsString = ""
    if res == "PROGRESS":
        bodyAsString = json.dumps(body.progress, ensure_ascii = False)
    elif res == "RESULTS":
        bodyAsString = json.dumps(body.computedResult, ensure_ascii=False)
    print("body as string {}".format(bodyAsString[:200]))
    msg = 'resolve::{}::{}::{}'.format(r, ID, res)
    if len(bodyAsString) > 0:
        msg += '@@' + bodyAsString

    queryRes = processQuery(uniqueID, r, msg)
    room = queryRes[0]
    resMsg = queryRes[1]

    return makeResponse(room = room, res = resMsg)
    
@app.get("/results/")
async def read(
    r : Annotated[str, "name of room"],
    ID: Annotated[str, "id of request when broadcasted"]
):
    uniqueID = communicationProcess.getUniqueID()
    msg = 'read::{}::{}'.format(r, ID)

    queryRes = processQuery(uniqueID, r, msg)
    room = queryRes[0]
    resMsg = queryRes[1]
    
    return makeResponse(room = room, res = resMsg)

@app.post("/close/")
async def close(
    r : Annotated[str, "name of room"] 
):
    uniqueID = communicationProcess.getUniqueID()
    msg = 'close::{}'.format(r)

    queryRes = processQuery(uniqueID, r, msg)
    room = queryRes[0]
    resMsg = queryRes[1]
    
    return makeResponse(room = room, res = resMsg)

@app.get("/status")
async def status():
    uniqueID = communicationProcess.getUniqueID()
    msg = 'status'

    queryRes = processQuery(uniqueID, '', msg)
    room = queryRes[0]
    resMsg = queryRes[1]
    
    return makeResponse(room = room, res = resMsg)

@app.post("/restart")
async def restart():
    if communicationProcess.__commProcess.is_alive():
        processQuery(-1, 'SYS', 'quit')
        time.sleep(1)
    
    communicationProcess.startProcess()

    return makeResponse(res='Command Registered')