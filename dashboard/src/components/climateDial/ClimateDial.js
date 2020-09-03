import React, { Component } from 'react'
import { GaugeChart } from "@carbon/charts-react";
import "@carbon/charts/styles.css";
import "./ibm-plex-font.css";
import { registerOnMessageCallback } from '../../../utils/wsConnector';

class FertilizerDial extends Component {
  constructor() {
    super();
    this.state = {data: [
    	{
    		"group": "value",
    		"value": 42
    	},
    	{
    		"group": "delta",
    		"value": -13.37
    	}
    ],
		options: {
    	"title": "Heat Level",
    	"resizable": true,
    	"height": "220px",
    	"width": "100%",
    	"gauge": { "type": "semi", "status": "danger"}
    }
   };
  }
	render() {
    return (
      <div>
        <GaugeChart
    			data={this.state.data}
    			options={this.state.options}>
    		</GaugeChart>
      </div>
	   )
  }
}
export default FertilizerDial
