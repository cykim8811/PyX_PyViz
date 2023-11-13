import { io } from 'socket.io-client';
const socket = io('http://code.cykim.site:7003');

const requests: { [key: string]: any } = {};

async function request(event: string, ...args: any[]): Promise<any> {
    return new Promise((resolve, reject) => {
        const requestId = Math.random().toString(36).substr(2, 9);
        requests[requestId] = { resolve, reject };
        socket.emit('request', event, requestId, ...args);
        setTimeout(() => {
            if (requests[requestId]) {
                requests[requestId].reject('timeout');
                delete requests[requestId];
            }
        }, 5000);
    });
}

// A request with cached data
const cachedRequests: { [key: string]: any } = {};
async function requestConst(event: string, ...args: any[]): Promise<any> {
    const hash = JSON.stringify([event, ...args]);
    if (cachedRequests[hash]) {
        return cachedRequests[hash];
    }
    const promise = request(event, ...args);
    promise.then((res) => {
        cachedRequests[hash] = res;
    });
    return promise;
}

socket.on('response', (msg: {[key: string]: any}) => {
    const requestId = msg.requestId;
    const data = msg.data;
    if (requests[requestId]) {
        requests[requestId].resolve(JSON.parse(data));
        delete requests[requestId];
    }
});

export const network = {
    socket,
    request,
    requestConst,
};

export type Network = typeof network;
