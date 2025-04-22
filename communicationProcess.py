# raise NotImplementedError("FInish this file or remove this line")

from collections import deque
import threading 

MAXSIMULTATNEOUSREQUESTS = 100000
EMPTY = 0
SUCCESS = 1
FAILURE = 2

class commQueue:
    def __init__(self):
        self.rooms = {}

        self.roomsMutex = threading.Lock()

    def broadcast(self, room, msg):
        with self.roomsMutex:
            if room not in self.rooms:
                return -1 
            
            self.rooms[room] = msg
        return 1

    def createRoom(self, room):
        with self.roomsMutex:
            if room in self.rooms:
                return -1
            self.rooms[room] = ''
        return 1

    def closeRoom(self, room):
        with self.roomsMutex:
            if room not in self.rooms:
                return -1
            del self.rooms[room]
        return 1
    
    def readBroadcast(self, room):
        with self.roomsMutex:
            if room not in self.rooms:
                return -1
            return self.rooms[room]
    
    def display(self):
        with self.roomsMutex:
            for room in self.rooms:
                print('room: {}'.format(room))
                print('\tval: {}'.format(self.rooms[room]))

__processQueue = commQueue()

__usedIDs = set()
idSafety = threading.Lock()
def getUniqueID():
    with idSafety:
        for i in range( MAXSIMULTATNEOUSREQUESTS ):
            if i not in __usedIDs:
                return i
    return -1

__serverRequests = deque()
def addRequest(ID, msg):
    with idSafety:
        __serverRequests.append((ID, msg))
        __usedIDs.add(ID)
def popRequest():
    with idSafety:
        return __serverRequests.popleft()

__serverResponses = {}
def addResponse(ID, msg):
    with idSafety:
        __serverResponses[ID] = msg
def responseAvailable(ID):
    with idSafety:
        return ID in __serverResponses and ID in __usedIDs
def popResponse(ID):
    with idSafety:
        if ID not in __usedIDs:
            return None
        __usedIDs.remove(ID)
        return __serverResponses[ID]

__commProcessRunning = True
__processMutex = threading.Lock()
def isCommProcessRunning():
    val = False
    with __processMutex:
        val = __commProcessRunning
    return val

def killProcess():
    with __processMutex:
        __commProcessRunning = False

def commProcess():
    val = isCommProcessRunning()
    while val:
        ID = -1
        res = None
        if len(__serverRequests) > 0:
            ID, req = popRequest()
            req_split = req.split("::")
            command = req_split[0]
            args = req_split[1:]
            if command == "broadcast":
                if len(args) != 2:
                    res = "Invalid format of 'broadcast'. Must be broadcast::<roomname>::<message>"

                roomname = args[0]
                broadcastMsg = args[1]
                retVal = __processQueue.broadcast(roomname, broadcastMsg)
                if retVal < 0:
                    res = "Room not found! {}".format(roomname)
                else:
                    res = "SUCCESS"

            elif command == "create":
                if len(args) != 1:
                    res = "Invalid format of 'broadcast'. Must be create::<roomname>"
                
                roomname = args[0]
                retVal = __processQueue.createRoom(roomname)
                if retVal < 0:
                    res = "Room already exists"
                else:
                    res = "SUCCESS"

            elif command == "read":
                if len(args) != 1:
                    res = "Invalid format of 'broadcast'. Must be read::<roomname>"
                
                roomname = args[0]
                retVal = __processQueue.readBroadcast(roomname)
                if isinstance(retVal, int) and retVal < 0:
                    res = "Room doesn't exists {}".format(roomname)
                else:
                    res = retVal

            elif command == "close":
                if len(args) != 1:
                    res = "Invalid format of 'broadcast'. Must be close::<roomname>"
                
                roomname = args[0]
                retVal = __processQueue.closeRoom(roomname)
                if retVal < 0:
                    res = "Room doesn't exists {}".format(roomname)
                else:
                    res = "SUCCESS"

            elif req.startswith("quit"):
                break
            else:
                res = "Invalid command {}".format(command)

        if ID != -1 and res is not None:
            addResponse(ID, res)
        val = isCommProcessRunning()

__commProcess = threading.Thread(target=commProcess, daemon=True)
def startProcess():
    __commProcess.start()