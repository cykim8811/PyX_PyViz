

pendingRender = []

setattrRegisteredClasses = []

def registerRenderable(obj):
    renderableObjects[id(obj)] = obj
    if type(obj) in setattrRegisteredClasses: return
    setattrRegisteredClasses.append(type(obj))
    objcls = type(obj)
    oldSetAttr = objcls.__setattr__
    def newsetattr(self, key, value):
        oldSetAttr(self, key, value)
        pendingRender.append(id(self))
    objcls.__setattr__ = newsetattr


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

def host(root, port=5000):
    requestHandler = RequestHandler()
    app = Flask(__name__)
    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*")
    registerRenderable(root)

    @app.route('/')
    def index():
        return 'XReact'

    @requestHandler.on('root')
    def getRoot():
        return id(root)

    @requestHandler.on('render')
    def render(id):
        user = {'isAdmin': True}
        if id not in renderableObjects: return None
        return renderableObjects[id].__render__(user)

    @socketio.on('call')
    def call(ftnId, *args):
        user = {'isAdmin': True}
        if ftnId not in callableObjects: return None
        ret = callableObjects[ftnId](*args)
        for id in pendingRender:
            socketio.emit('render', {'id': id, 'data': renderableObjects[id].__render__(user)})
        pendingRender.clear()
        return ret

    @socketio.on('request')
    def req(event, requestId, *args):
        res = requestHandler[event](*args)
        socketio.emit('response', {'requestId': requestId, 'data': json.dumps(res)}, room=request.sid)

    socketio.run(app, host='0.0.0.0', port=port)
