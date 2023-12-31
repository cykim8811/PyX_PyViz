

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
    
    def __contains__(self, key):
        return key in self.data

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
def createElement(tag, props=None, *children):
    if len(children) == 1 and type(children[0]) is list:
        children = children[0]
    if props is None:
        props = {}
    for key in props:
        target = props[key]
        if type(target) == type(lambda: 0) or type(target) == type(lambda: 0).__call__:
            callableObjects[id(target)] = target
            props[key] = {'__call__': id(target), 'preventDefault': target.preventDefault if hasattr(target, 'preventDefault') else False, 'stopPropagation': target.stopPropagation if hasattr(target, 'stopPropagation') else False, 'returnFormat': target.returnFormat if hasattr(target, 'returnFormat') else None}
            if not hasattr(target, 'returnFormat'):
                print('WARNING: No returnFormat specified for', target)
    children = [child for child in children if child is not None]
    for i in range(len(children)):
        if hasattr(children[i], '__render__'):
            registerRenderable(children[i])
            children[i] = id(children[i])
        elif type(children[i]) is int:
            children[i] = str(children[i])
    return {
        'tag': tag,
        'props': props,
        'children': children
    }


from flask import Flask, request, Response
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

import sys
import inspect
import os

roots = {}
root_refcount = {}

def get_room(name, root_generator=None):
    if name not in roots:
        roots[name] = root_generator()
        registerRenderable(roots[name])
    return roots[name]

import randomname

def get_random_room_name():
    return randomname.get_name()

def host(root_generator, port):
    requestHandler = RequestHandler()

    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    dir_path = os.path.dirname(os.path.abspath(module.__file__))


    app = Flask(__name__, static_folder=dir_path+'/dist')
    socketio = SocketIO(app, cors_allowed_origins="*")

    userList = {}

    def getUser(sid):
        if sid not in userList:
            userList[sid] = User(sid)
        return userList[sid]

    @app.route('/')
    def index():
        if request.args.get('room') is None:
            return f'<script>window.location.href = "/?room={get_random_room_name()}";</script>'
            
        return app.send_static_file('index.html')
    
    @app.route('/<path:path>')
    def serve_dist(path):
        return app.send_static_file(path)
    
    @app.route('/engine.js')
    def serve_engine():
        dir_path = os.path.dirname(os.path.abspath(__file__))
        with open(dir_path+'/dist/engine.js') as f:
            content = f.read()
        return Response(content, mimetype='application/javascript')

    @requestHandler.on('root')
    def getRoot(roomname):
        user = getUser(request.sid)
        if 'room' not in user.data:
            user['room'] = get_room(roomname, root_generator)
            user['roomname'] = roomname
            if roomname not in root_refcount:
                print(f"Room created: {roomname:3s} - {root_refcount}")
            root_refcount[roomname] = root_refcount[roomname] + 1 if roomname in root_refcount else 1
        return id(user.room)

    @requestHandler.on('render')
    def render(id):
        user = getUser(request.sid)
        if id not in renderableObjects: return None
        return user.render(renderableObjects[id])

    @socketio.on('call')
    def call(ftnId, *args):
        global pendingRender
        user = getUser(request.sid)
        if ftnId not in callableObjects: return None
        ret = callableObjects[ftnId](*args)
        while len(pendingRender) > 0:
            current_render = pendingRender
            pendingRender = {}
            for renderable_id in current_render:
                if current_render[renderable_id] == []:
                    current_render[renderable_id] = list(userList.keys())
                for user_id in current_render[renderable_id]:
                    if renderable_id not in renderableObjects:
                        import ctypes
                        print("RENDERABLE NOT FOUND", renderable_id, ctypes.cast(renderable_id, ctypes.py_object).value)
                        continue
                    ret = getUser(user_id).render(renderableObjects[renderable_id])
                    socketio.emit('render', {'id': renderable_id, 'data': ret}, room=user_id)
        pendingRender.clear()
        return ret

    @socketio.on('request')
    def req(event, requestId, *args):
        res = requestHandler[event](*args)
        socketio.emit('response', {'requestId': requestId, 'data': json.dumps(res)}, room=request.sid)

    @socketio.on('disconnect')
    def disconnect():
        user = getUser(request.sid)
        if request.sid in userList:
            if 'room' in user:
                room_id = user['roomname'] if 'roomname' in user else None
                if room_id is not None:
                    root_refcount[room_id] -= 1
                    if root_refcount[room_id] == 0:
                        del roots[room_id]
                        del root_refcount[room_id]
                        print(f"Room deleted: {room_id:3s} - {root_refcount}")
            del userList[request.sid]
            
    socketio.run(app, host='0.0.0.0', port=port)
