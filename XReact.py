

pendingRender = {}
# pendingRender: {renderable_id: [user_id, user_id, ...], ...}

def registerPendingRender(renderable_id, user_id='all'):
    if type(renderable_id) is not int:
        raise TypeError('renderable_id must be int')
    if type(user_id) is not str:
        raise TypeError('user_id must be str')
    if renderable_id not in pendingRender:
        pendingRender[renderable_id] = []
    if user_id == 'all':
        pendingRender[renderable_id] = [] # all users
        return
    if user_id not in pendingRender[renderable_id]:
        pendingRender[renderable_id].append(user_id)
    

setattrRegisteredClasses = []

def registerRenderable(obj):
    renderableObjects[id(obj)] = obj
    if type(obj) in setattrRegisteredClasses: return
    setattrRegisteredClasses.append(type(obj))
    objcls = type(obj)
    oldSetAttr = objcls.__setattr__
    def newsetattr(self, key, value):
        oldSetAttr(self, key, value)
        registerPendingRender(id(self))
    objcls.__setattr__ = newsetattr

class User:
    def __init__(self, sid):
        self.__dict__['data'] = {}
        self.__dict__['__currentRender'] = None
        self.__dict__['dependencies'] = {}  # {key: [renderable_id, renderable_id, ...], ...}
        self.__dict__['sid'] = sid

    def __getattr__(self, key):
        __currentRender = self.__dict__['__currentRender']
        if __currentRender is not None:
            if id(__currentRender) not in self.dependencies:
                self.dependencies[key] = []
            self.dependencies[key].append(id(__currentRender))
        return self.data[key] if key in self.data else None

    def __setattr__(self, key, value):
        self.data[key] = value
        if key not in self.dependencies: return
        for dependency in self.dependencies[key]:
            registerPendingRender(dependency, self.__dict__['sid'])

    def __getitem__(self, key):
        __currentRender = self.__dict__['__currentRender']
        if __currentRender is not None:
            if id(__currentRender) not in self.dependencies:
                self.dependencies[key] = []
            self.dependencies[key].append(id(__currentRender))
        return self.data[key] if key in self.data else None

    def __setitem__(self, key, value):
        self.data[key] = value
        if key not in self.dependencies: return
        for dependency in self.dependencies[key]:
            registerPendingRender(dependency, id(self))

    def render(self, renderable):
        self.__dict__['__currentRender'] = renderable
        ret = renderable.__render__(self)
        self.__dict__['__currentRender'] = None
        return ret


renderableObjects = {}
callableObjects = {}
def createElement(tag, props, *children):
    for key in props:
        target = props[key]
        if type(target) == type(lambda: 0):
            callableObjects[id(target)] = target
            props[key] = {'__call__': id(target)}
    children = list(children)
    for i in range(len(children)):
        if hasattr(children[i], '__render__'):
            registerRenderable(children[i])
            children[i] = id(children[i])
    return {
        'tag': tag,
        'props': props,
        'children': children
    }


from flask import Flask, request
from flask_socketio import SocketIO
from flask_cors import CORS
import json

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class RequestHandler:
    def __init__(self):
        self.requests = {}

    def on(self, event):
        def decorator(func):
            self.requests[event] = func
            return func
        return decorator

    def __getitem__(self, event):
        return self.requests[event]

def host(root, port):
    requestHandler = RequestHandler()
    app = Flask(__name__, static_folder='dist')
    socketio = SocketIO(app, cors_allowed_origins="*")
    registerRenderable(root)

    userList = {}

    def getUser(sid):
        if sid not in userList:
            userList[sid] = User(sid)
        return userList[sid]

    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    @app.route('/<path:path>')
    def serve_dist(path):
        return app.send_static_file(path)

    @requestHandler.on('root')
    def getRoot():
        return id(root)

    @requestHandler.on('render')
    def render(id):
        user = getUser(request.sid)
        if id not in renderableObjects: return None
        return user.render(renderableObjects[id])

    @socketio.on('call')
    def call(ftnId, *args):
        user = getUser(request.sid)
        if ftnId not in callableObjects: return None
        ret = callableObjects[ftnId](*args)
        for renderable_id in pendingRender:
            if pendingRender[renderable_id] == []:
                pendingRender[renderable_id] = list(userList.keys())
            for user_id in pendingRender[renderable_id]:
                ret = getUser(user_id).render(renderableObjects[renderable_id])
                socketio.emit('render', {'id': renderable_id, 'data': ret}, room=user_id)
        pendingRender.clear()
        return ret

    @socketio.on('request')
    def req(event, requestId, *args):
        res = requestHandler[event](*args)
        socketio.emit('response', {'requestId': requestId, 'data': json.dumps(res)}, room=request.sid)

    socketio.run(app, host='0.0.0.0', port=port)
