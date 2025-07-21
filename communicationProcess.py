# raise NotImplementedError("FInish this file or remove this line")

from collections import deque
import threading 
import time
import uuid

MAXSIMULTATNEOUSREQUESTS = 100000
BROADCASTDURATION = 10 
RESOLUTIONTIMER = 30

PONGRESPONSETIMER = 20
PINGCHECKTIMER = 60

EMPTY = 0
SUCCESS = 1
FAILURE = 2

class commQueue:
    def __init__(self):
        '''
        format:
        {
            <roomname>:{
                'results': {
                    <resolution id>: <resolution msg>,
                    ...
                },

                # from here its the query
                <first query>: <resolution id>,
                ...
            }
        }
        i.e.)
        simpleapp: {'results': {}, '4b3b9864-00d1-4b36-bc7a-ae630df00551': 'ping'}
        '''
        self.rooms = {}
        '''
        format:
        {
            <resolution id>: <time at broadcast() call>,
            ...
        }
        '''
        self.idTimerBroadcast = {}
        '''
        format:
        {
            <resolution id>: <time at resolve() call>,
            ...
        }
        '''
        self.idTimerResolution = {}

        self.roomsMutex = threading.Lock()

    def broadcast(self, room, ID, msg):
        with self.roomsMutex:
            if room not in self.rooms:
                return -1 
            
            self.rooms[room][ID] = msg
            self.idTimerBroadcast[ID] = time.time()

        return 1

    def resolve(self, room, ID, msg):
        with self.roomsMutex:
            if room not in self.rooms:
                return -1 
            
            self.rooms[room]['results'][ID] = msg
            self.idTimerResolution[ID] = time.time()
        return 1

    def createRoom(self, room):
        with self.roomsMutex:
            if room in self.rooms:
                return -1
            self.rooms[room] = {}
            self.rooms[room]['results'] = {}
        return 1

    def closeRoom(self, room):
        with self.roomsMutex:
            if room not in self.rooms:
                return -1
            del self.rooms[room]
        return 1
    
    def readResult(self, room, resultID):
        with self.roomsMutex:
            #print('READRESULT: ', self.rooms)
            if room not in self.rooms:
                return -1
            elif resultID not in self.rooms[room]['results']:
                return -1
            #print('ROOMS in result:',self.rooms[room])
            return self.rooms[room]['results'][resultID]
    
    def readBroadcasts(self, room):
        with self.roomsMutex:
            #print('READBROADCASTS ({}): {}'.format(room, self.rooms))
            if room not in self.rooms:
                return -1
            retVal = {}
            for key in self.rooms[room]:
                if key == 'results':
                    continue
                retVal[key] = self.rooms[room][key]
            return retVal
    
    def checkForTimer(self):
        with self.roomsMutex:
            for room in self.rooms:
                toDelete = []
                for ID in self.rooms[room]:
                    if ID == 'results':
                        continue
                    # print('rooms ', self.rooms)
                    # print('broadcastTimers: ', self.idTimerBroadcast)
                    if time.time() - self.idTimerBroadcast[ID] > BROADCASTDURATION:
                        toDelete.append(ID) 
                for item in toDelete:
                    del self.rooms[room][item]
                    del self.idTimerBroadcast[item]

                toDelete.clear()
                for ID in self.rooms[room]['results']:
                    if time.time() - self.idTimerResolution[ID] > RESOLUTIONTIMER:
                        toDelete.append(ID) 
                for item in toDelete:
                    del self.rooms[room]['results'][item]
                    del self.idTimerResolution[item]

    
    '''
    {
        "room": "",
        "res": "room: simpleapp\n\tval: {'results': {}, '4b3b9864-00d1-4b36-bc7a-ae630df00551': 'ping'}"
    }
    '''
    def display(self):
        retval = []
        with self.roomsMutex:
            for room in self.rooms:
                retval.append('room: {}'.format(room))
                retval.append('\tval: {}'.format(self.rooms[room]))
        return '\n'.join(retval)

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
def addRequest(ID, roomname, msg):
    with idSafety:
        __serverRequests.append((ID, roomname, msg))
def popRequest():
    with idSafety:
        return __serverRequests.popleft()

'''
Format is 
{
    <ID>: (<roomname>, <msg>),
    ...
}
'''
__serverResponses = {}
def addResponse(ID, roomname, msg):
    print("Adding: ",msg)
    with idSafety:
        __serverResponses[ID] = (roomname, msg)
        __usedIDs.add(ID)
def responseAvailable(ID):
    with idSafety:
        return ID in __serverResponses and ID in __usedIDs
def popResponse(ID):
    with idSafety:
        if ID not in __usedIDs:
            return None
        __usedIDs.remove(ID)
        print("Returning: ",__serverResponses[ID])
        # (roomname, msg)
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

def closeEverything():
    with __processQueue.roomsMutex:
        __processQueue.rooms = {}
        __processQueue.idTimerBroadcast = {}
        __processQueue.idTimerResolution = {}
    with idSafety:
        __usedIDs.clear()
        __serverRequests.clear()
        __serverResposes.clear()
    with pingedMutex:
        pinged.clear()

'''
format:
{
    <id of resolution - the unique long one>: {
        'roomname': <roomname>,
        'time': <time when pinged>
    },
    ...
}
'''
# The method is this:
# We have 2 kinds timers:
#   - one for a regular ping check
#   - and many for a response check
#      (The resolutions and broadcasts disappear in the "checkForTimer function of commProcess")
pinged = {}
pingedMutex = threading.Lock()
def roomChecker():
    print('ROOM CHECK: This is a separate thread that regularly pings the rooms')
    print('ROOM CHECK: Make sure your programs have the ability to ping back')
    responseTimer = 10 # time it takes to check the response
    print('ROOM CHECK: The time for a response within this server itself is {} seconds'.format(responseTimer))
    pingStartTime = time.time()

    pingCheckStartTime = time.time()

    isRunning = isCommProcessRunning()
    while isRunning:
        # print('Time left to ping: {:0.3f}'.format(PINGCHECKTIMER - time.time() + pingStartTime))
        if time.time() - pingStartTime > PINGCHECKTIMER:
            print("PINGING!")
            # send a 'ping' command and keep track of all the ids
            # (pings EVERY room)
            pingedIDs = deque() 
            with __processQueue.roomsMutex: 
                for room in __processQueue.rooms.keys():
                    newID = getUniqueID()
                    addRequest(newID, room, 'broadcast::{}::ping'.format(room))
                    pingedIDs.append(newID)
            time.sleep(3) # letting the responses sit a little so the 
                            # process can pick it up 
            # checking if the server is processing the 'ping' command
            # (this should be in the response listing)
            while len(pingedIDs) > 0:
                idToCheck = pingedIDs.popleft()
                idCheckTime = time.time()
                # a way to see if a response was found
                while not responseAvailable(idToCheck):
                    print('TIME ELAPSED FOR A RESPONSE: {}s'.format(time.time() - idCheckTIme))
                    if time.time() - idCheckTime > responseTimer:
                        print('ROOM CHECK: >>>server might be dead<<<')
                        print('ROOM CHECK: Time to check id took too long')
                        print('ROOM CHECK: id was {}'.format(idToCheck))
                        # quits the whole application
                        return 
                response = popResponse(idToCheck)
                pingUUID = response[1]
                #print('RESPONSE:', response)
                #This means ping was successful
                with pingedMutex:
                    pinged[idToCheck] = {'roomname':response[0], 'pingUUID':pingUUID, 'time':time.time()}
                    print("ROOMCHECK: PINGED vvvvvv")
                    print(pinged)
            pingStartTime = time.time()


        with pingedMutex:
            idProcessed = []
            for ID in pinged.keys():
                #print("ROOMCHECK: For {}: {}s leftover".format(ID, PONGRESPONSETIMER - time.time() + pinged[ID]['time']))
                if time.time() - pinged[ID]['time'] <= PONGRESPONSETIMER:
                    # check to see if there a resolving 'pong' response
                    #allCurrentBroadcasts = __processQueue.readBroadcasts(pinged[ID]['roomname'])
                    #print('All current broadcasts:', allCurrentBroadcasts)
                    roomResponse = __processQueue.readResult(pinged[ID]['roomname'], pinged[ID]['pingUUID'])
                    #print('current responses:', roomResponse)
                    pongFound = False
                    if isinstance(roomResponse , str):
                        if roomResponse == 'pong':
                            pongFound = True
                        if pongFound:
                            print('>>>>>>>[^ - ^]>>>>>>>>>>>PONG FOUND')
                    if pongFound:
                        # we found a pong, so dont delete the room
                        idProcessed.append(ID)
                    else:
                        # adding a "hole" in case we want to know if we alloted
                        # space for the possibility when 
                        #   neither pong was found and if the time was within the pong response timer
                        pass
                else:
                    # there is no 'pong' response so we shut this room down
                    # we delete all the rooms to close
                    __processQueue.closeRoom(pinged[ID]['roomname'])
                    idProcessed.append(ID)
            # remove all registered PINGs
            # the 'pong' (so it can ping again)
            for ID in idProcessed:
                del pinged[ID]
        # print(isCommProcessRunning())
        isRunning = isCommProcessRunning()

def commProcess():
    isRunning = isCommProcessRunning()
    while isRunning:
        __processQueue.checkForTimer()

        ID = -1
        res = None
        serverRequestSize = 0
        with idSafety:
            serverRequestSize = len(__serverRequests)
        if serverRequestSize > 0:
            ID, roomname, req = popRequest()
            req_split = req.split("::")
            command = req_split[0]
            args = req_split[1:]
            if command == "broadcast":
                if len(args) != 2:
                    roomname = 'SYS'
                    res = "ERROR: Invalid format of 'broadcast'. Must be broadcast::<roomname>::<message>"

                broadcastMsg = args[1]
                specialID = str(uuid.uuid4())
                retVal = __processQueue.broadcast(roomname, specialID, broadcastMsg)
                if retVal < 0:
                    roomname = 'SYS'
                    res = "ERROR: Room not found! {}".format(roomname)
                else:
                    res = specialID

            elif command == "getbroadcast":
                if len(args) != 1:
                    roomname = 'SYS'
                    res = "ERROR: Invalid format of 'getbroadcast'. Must be getbroadcast::<roomname>"
                retVal = __processQueue.readBroadcasts(roomname)
                if isinstance(retVal,int) and retVal < 0:
                    roomname = 'SYS'
                    res = "ERROR: Room not found! {}".format(roomname)
                else:
                    res = retVal

            elif command == "create":
                if len(args) != 1:
                    roomname = 'SYS'
                    res = "ERROR: Invalid format of 'broadcast'. Must be create::<roomname>"
                
                retVal = __processQueue.createRoom(roomname)
                if retVal < 0:
                    roomname = 'SYS'
                    res = "ERROR: Room already exists"
                else:
                    res = "SUCCESS"

            elif command == "resolve":
                if len(args) != 3:
                    roomname = 'SYS'
                    res = "ERROR: Invalid format of 'resolution'. Must be resolution::<roomname>::<id>::<resolution>"
                
                requestID = args[1]
                msg = args[2]
                retVal = __processQueue.resolve(roomname, requestID, msg)
                if isinstance(retVal, int) and retVal < 0:
                    roomname = 'SYS'
                    res = "ERROR: Room doesn't exists {}".format(roomname)
                else:
                    res = retVal

            elif command == "read":
                if len(args) != 2:
                    roomname = 'SYS'
                    res = "ERROR: Invalid format of 'broadcast'. Must be read::<roomname>"
                
                requestID = args[1]
                retVal = __processQueue.readResult(roomname, requestID)
                if isinstance(retVal, int) and retVal < 0:
                    roomname = 'SYS'
                    res = "ERROR: Room doesn't exists {}".format(roomname)
                else:
                    res = retVal

            elif command == "close":
                if len(args) != 1:
                    roomname = 'SYS'
                    res = "ERROR: Invalid format of 'broadcast'. Must be close::<roomname>"
                
                retVal = __processQueue.closeRoom(roomname)
                if retVal < 0:
                    roomname = 'SYS'
                    res = "ERROR: Room doesn't exists {}".format(roomname)
                else:
                    res = "SUCCESS"

            elif command == "status":
                if len(args) != 0:
                    roomname = 'SYS'
                    res = "ERROR: Invalid format of 'status'. Must be status"

                res = __processQueue.display()

            elif command == "quit":
                closeEverythin()
                break
            else:
                roomname = 'SYS'
                res = "ERROR: Invalid command {}".format(command)

            if ID != -1 and res is not None:
                addResponse(ID, roomname, res)
        isRunning = isCommProcessRunning()

global __commProcess
__commProcess = None 

global __pingCheckProcess
__pingCheckProcess = None
def startProcess():
    print('Starting background thread')
    global __commProcess
    __commProcess = threading.Thread(target=commProcess)
    __commProcess.daemon = True
    __commProcess.start()

    global __pingCheckProcess
    __pingCheckProcess = threading.Thread(target=roomChecker)
    __pingCheckProcess.daemon = True
    __pingCheckProcess.start()
    # print("Var in question ", __commProcess)
