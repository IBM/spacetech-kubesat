import React, { Component } from 'react'
import "@carbon/charts/styles-g100.css";
import "./ibm-plex-font.css";
import { GaugeChart } from "@carbon/charts-react";
import {Grid, Row, Column, Dropdown} from "carbon-components-react";
import { registerOnMessageCallback } from '../../utils/wsConnector';
import "./dial.css";

class Dial extends Component {
  constructor() {
    super();
    this.dashboardPress = this.dashboardPress.bind(this);
    this.state = {
        dropdownItems: [],
        data: {
          init: {
            temperature: {
              value: 0,
              delta: 0
            },
            moisture: {
              value: 0,
              delta: 0
            },
            fertilization: {
              value: 0,
              delta: 0
            }
          }
        },
        selectedIOT: "init",
      };
    registerOnMessageCallback("received.temperature", (message) => this.updateTemp.bind(this)(message));
    registerOnMessageCallback("received.soil_water_content", (message) => this.updateWater.bind(this)(message));
    registerOnMessageCallback("received.fertilization", (message) => this.updateFertilization.bind(this)(message));
  }

  updateTemp(data){
    //add entry if doesn't exist
    if(! this.state.data.hasOwnProperty(data.origin_ID)){
      let new_data = this.state.data
      new_data[data.origin_ID] = {
                                  temperature: {
                                    value: data.data,
                                    delta: 0
                                  },
                                  moisture: {
                                    value: 0,
                                    delta: 0
                                  },
                                  fertilization: {
                                    value: 0,
                                    delta: 0
                                  }
                                };
      this.setState({data: new_data});
      let new_dropdown = this.state.dropdownItems
      new_dropdown.push({id: data.origin_ID, label: data.origin_ID})
      this.setState({dropdownItems: new_dropdown})
    } else {
      //update large percent
      let new_data = this.state.data[data.origin_ID];
      new_data.temperature.delta = data.data - new_data.temperature.value
      new_data.temperature.value = data.data
      let new_state = this.state.data
      new_state[data.origin_ID] = new_data
      this.setState({data: new_state})
    }
  }

  updateWater(data){
    if(! this.state.data.hasOwnProperty(data.origin_ID)){
      let new_data = this.state.data
      new_data[data.origin_ID] = {
        temperature: {
          value: 0,
          delta: 0
        },
        moisture: {
          value: data.data,
          delta: 0
        },
        fertilization: {
          value: 0,
          delta: 0
        }
      };
      this.setState({data: new_data});
      let new_dropdown = this.state.dropdownItems
      new_dropdown.push({id: data.origin_ID, label: data.origin_ID})
      this.setState({dropdownItems: new_dropdown})
    } else {
    //update large percent
      let new_data = this.state.data[data.origin_ID];
      new_data.moisture.delta = data.data - new_data.moisture.value
      new_data.moisture.value = data.data
      let new_state = this.state.data
      new_state[data.origin_ID] = new_data
      this.setState({data: new_state})
    }
  }

  updateFertilization(data){
     //add entry if doesn't exist
     if(! this.state.data.hasOwnProperty(data.origin_ID)){
      let new_data = this.state.data
      new_data[data.origin_ID] = {
        temperature: {
          value: 0,
          delta: 0
        },
        moisture: {
          value: 0,
          delta: 0
        },
        fertilization: {
          value: data.data * 100,
          delta: 0
        }
      };
      this.setState({data: new_data});
      let new_dropdown = this.state.dropdownItems
      new_dropdown.push({id: data.origin_ID, label: data.origin_ID})
      this.setState({dropdownItems: new_dropdown})
    } else {
      //update large percent
        let new_data = this.state.data[data.origin_ID];
        new_data.fertilization.delta = data.data * 100 - new_data.fertilization.value
        new_data.fertilization.value = data.data * 100
        let new_state = this.state.data
        new_state[data.origin_ID] = new_data
        this.setState({data: new_state})
      }
  }

  dashboardPress(event) {
    this.setState({selectedIOT: event.selectedItem.id,});
   }

	render() {
    return (
      <div className="bx--col right-shift">
        <Dropdown
          ariaLabel="Dropdown"
          id="object-selection-dropdown"
          items={this.state.dropdownItems}
          label="Select IOT Sensor"
          onChange={(e) => this.dashboardPress(e)}/>
        <div className="bx--row bx--grid--condensed sub-dial-system">
          <div className="bx--col">
            <div className="sub-dial-middle-padding">
              <GaugeChart
                data={[{group: "value", value: this.state.data[this.state.selectedIOT].fertilization.value},
                       {group: "delta", value: this.state.data[this.state.selectedIOT].fertilization.delta}]}
                options={{
                  title: "Nutrient Index",
                  resizable: true,
                  height: "170px",
                  width: "100%",
                  gauge: {
                    type: "semi",
                    status: "danger"
                  }
                }}>
            </GaugeChart>
            </div>
          </div>
          <div className="bx--col">
            <div className="sub-dial-middle-padding">
              <GaugeChart
                data={[{group: "value", value: this.state.data[this.state.selectedIOT].temperature.value},
                       {group: "delta", value: this.state.data[this.state.selectedIOT].temperature.delta}]}
                options={{
                  title: "Heat Index",
                  resizable: true,
                  height: "170px",
                  width: "100%",
                  gauge: {
                    type: "semi",
                    status: "danger"
                  }
                }}>
              </GaugeChart>
            </div>
          </div>
          <div className="bx--col">
            <div className="sub-dial-middle-padding">
              <GaugeChart
                data={[{group: "value", value: this.state.data[this.state.selectedIOT].moisture.value},
                       {group: "delta", value: this.state.data[this.state.selectedIOT].moisture.delta}]}
                options={{
                  title: "Moisture Index",
                  resizable: true,
                  height: "170px",
                  width: "100%",
                  gauge: {
                    type: "semi",
                    status: "danger"
                  }
                }}>
              </GaugeChart>
            </div>
          </div>
        </div>
      </div>
	   )
  }
}
export default Dial
