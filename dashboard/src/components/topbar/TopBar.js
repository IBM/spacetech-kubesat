import React, { Component } from 'react'
import {  Header,
          HeaderName,
          HeaderNavigation,
          HeaderMenu,
          HeaderMenuItem,
          HeaderGlobalAction,
          HeaderGlobalBar
} from "carbon-components-react/lib/components/UIShell";
import { Download20 } from '@carbon/icons-react';
import { registerOnMessageCallback } from '../../utils/wsConnector'
import {CSVLink, CSVDownload} from 'react-csv';

const columns = [
   {
       Header: 'name',
       accessor: 'name',
   },
   {
       Header: 'age',
       accessor: 'age',

  }];

class TopBar extends Component {
  constructor() {
    super();
    this.state = {time: "",
                  data: [],
                  downloadStepCount: 0,
                };
    registerOnMessageCallback("simulation.timestep", (message) => this.updateData.bind(this)(message.data))
  }

  updateData(data) {
    var count = this.state.downloadStepCount + 1;
    this.setState({time: data.time, downloadStepCount: count});
    if (count % 10 === 0){
      var dataUpdated = this.state.data;
      dataUpdated.push({time: data.time})
      this.setState({data: dataUpdated});
    }
  }

  render() {
    return (
      <div>
        <Header aria-label="IBM gg">
          <HeaderName href="#" prefix="IBM">
            Software Defined Satellite Swarm
          </HeaderName>
          <HeaderNavigation aria-label="IBM [Platform]">
            <HeaderMenuItem href="#"> {this.state.time} UTC </HeaderMenuItem>
          </HeaderNavigation>
          <HeaderGlobalBar>
            <HeaderGlobalAction
              aria-label="Download">
              <CSVLink
                    data={this.state.data}
                    filename="IBMSpaceTech_SatSwarmData.csv"
                    target="_blank">
                <Download20
                style={{color:'white'}}/>
              </CSVLink>
            </HeaderGlobalAction>
          </HeaderGlobalBar>
        </Header>
      </div>
    )
  }
}

export default TopBar
