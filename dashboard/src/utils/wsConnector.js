import React, { Component } from 'react'

const URL = 'ws://'+ window.location.host + '/api/streaming'
console.log(URL)

let onMessageCallbacks = [];

export const startWebsocketConnection = () => {
  const ws = new window.WebSocket(URL) || {}

  ws.onopen = () => {
    console.log('opened ws connection')
  }

  ws.onmessage = (e) => {
    let message = JSON.parse(e.data);
    onMessageCallbacks.forEach((cb) => {
      if (message.subject === cb[0]){
        cb[1](message.msg)
      }
    });
  }

  ws.onclose = function(e) {
    console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
    setTimeout(function() {
      startWebsocketConnection();
    }, 1000);
  };

  ws.onerror = function(err) {
    console.error('Socket encountered error: ', err.message, 'Closing socket');
    ws.close();
  };
}

export const registerOnMessageCallback = (topic, fn) => {
  onMessageCallbacks.push([topic, fn]);
  console.log("registered callback")
  console.log(onMessageCallbacks)
}
