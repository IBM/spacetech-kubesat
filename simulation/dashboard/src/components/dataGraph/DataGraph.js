import React, { Component } from 'react'
import { StackedAreaChart } from "@carbon/charts-react";
import "@carbon/charts/styles.css";
import {g100} from '@carbon/themes';
import { registerOnMessageCallback } from '../../utils/wsConnector';


class DataGraph extends Component {
  constructor() {
    super();
    this.state = {
      data: [],
      options: {
        "axes": {
          "left": {"stacked": true, "scaleType": "linear", "mapsTo": "value", "title": "Packets Received",
          },
          "bottom": {"scaleType": "time", "mapsTo": "date"},
        },
        "curve": "curveMonotoneX",
        "height": "230px",
        "width": "100%",
        "resizable": true,
      },
      phonebook: {},
    }
    registerOnMessageCallback("groundstation.packets_received", (message) => this.updateData.bind(this)(message))
  }

  updateData(data){

    var receivingGroundStation = data.origin_ID;
    var sendDate = data.time_sent;
    if ((this.state.data.length === 0) || (!((this.state.data[this.state.data.length - 1].date === sendDate) && (this.state.data[this.state.data.length - 1].group === receivingGroundStation)))){
      var tempPhoneBook = this.state.phonebook;
      var key = data.origin_ID;
      if (tempPhoneBook.hasOwnProperty(key)){
        tempPhoneBook[key] = (tempPhoneBook[key] + data.data);
      }
      else{
        tempPhoneBook[key] = data.data;
      }
      var tempData = this.state.data;
      tempData.push({"group": receivingGroundStation, "date": sendDate, "value": tempPhoneBook[key],});
      this.setState({phonebook: tempPhoneBook});
      this.setState({data: tempData});
    }
  }


	render() {
    return (
      <div class="graph-shift-down">
    		<StackedAreaChart
    			data={this.state.data}
    			options={this.state.options}>
    		</StackedAreaChart>
      </div>
	   )
  }
}
export default DataGraph
