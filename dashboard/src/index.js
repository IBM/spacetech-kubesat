import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './components/app/App';
import './index.scss';
import {startWebsocketConnection} from './utils/wsConnector'
//import "core-js/modules/es7.array.includes";
//import "core-js/modules/es6.array.fill";
//import "core-js/modules/es6.string.includes";
//import "core-js/modules/es6.string.trim";
//import "core-js/modules/es7.object.values";
startWebsocketConnection();
ReactDOM.render(<App />, document.getElementById('root'));
// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
