import "./app.scss";
import './App.css';
import React, { Component } from 'react';
import {Grid, Row, Column} from "carbon-components-react";
import TopBar from '../topbar/TopBar'
import TabledObjects from '../table/TabledObjects'
import Globe from '../globe/Globe'
import DataGraph from '../dataGraph/DataGraph'
import MapChart from '../mapChart/MapChart'

import Dial from '../dial/Dial'
import FadeIn from "react-fade-in";
import Lottie from "react-lottie";
import {g100} from '@carbon/themes';
import { registerOnMessageCallback } from '../../utils/wsConnector';

class App extends Component {
  constructor(){
     super();
     this.state = {
        done: false //undefined
     };
     this.setTrue = this.setTrue.bind(this);
  }

  componentDidMount() {
    this.countdown = setInterval(this.setTrue, 3500);
  };


  setTrue(){
    this.setState({done: true});
    clearInterval(this.countdown);
  }

  render() {
    return (
      <div>
         {!this.state.done ? (
          <FadeIn>
            <div className="intro">
            </div>
          </FadeIn>
         ) : (
           <FadeIn>
             <div className="bx--grid">
                 <div className="bx--row top-bar">
                   <TopBar/>
                 </div>
                 <div className="bx--row">
                   <div class="bx--col-lg-7">
                     <Globe/>
                     <div className="data-graph">
                      <DataGraph width='100%' />
                     </div>
                   </div>
                   <div class="bx--col-lg-4">
                      <div className="bx--row">
                        <TabledObjects/>
                      </div>
                      <div className="bx--row shift-dial-system">
                        <Dial/>
                      </div>
                   </div>
                 </div>
             </div>
            </FadeIn>
         )}
      </div>
    );
  }
}

export default App;
