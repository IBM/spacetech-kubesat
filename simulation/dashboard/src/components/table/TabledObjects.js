import React, { Component } from 'react'
import { Button,
         DataTable,
         TableContainer,
         Table,
         TableHead,
         TableRow,
         TableHeader,
         TableBody,
         TableCell,
         Dropdown
 } from "carbon-components-react";
 import { registerOnMessageCallback } from '../../utils/wsConnector'

 class TabledObjects extends Component {

   constructor() {
     super();
     this.dashboardPress = this.dashboardPress.bind(this);
     this.state = {
        rowData: {start: [{id: ""},], },
        selectedRow: "start",
        ColumnData: {start: [{header: "", key: "id"}], },
        dropdownItems: [],
        phonebook: {},
        curTime: "",
     }
     registerOnMessageCallback("state", (message) => this.updateRows.bind(this)(message));
     registerOnMessageCallback("simulation.timestep", (message) => this.updateTime.bind(this)(message.data));
     registerOnMessageCallback("received.battery_percentage", (message) => this.updateBattery.bind(this)(message));
   }

   updateBattery(data) {
     var tempPhoneBook = this.state.phonebook;
     tempPhoneBook[data.origin_ID] = data.data;
     this.setState({phonebook: tempPhoneBook});
   }

   updateRows(data) {
     var key = data.sender_ID;
     if (!(this.state.phonebook.hasOwnProperty(data.sender_ID))){
       //update phonebook
       var tempPhoneBook = this.state.phonebook;
       tempPhoneBook[key] = "pending";
       this.setState({phonebook: tempPhoneBook});
       //create new dropdown item
       var tempDropDown = this.state.dropdownItems;
       tempDropDown.push({id: data.sender_ID, label: data.sender_ID});
       this.setState({dropdownItems: tempDropDown});
     }
     //create or update new row dataset
     var pointing = "Pointing to: ";
     try {
        pointing = pointing.concat(data.data.state[key].orbit.attitude)
        var targetInView = "Target in View: ";
        if (data.data.state[key].target_in_view){
          targetInView = targetInView.concat("True");
        }
        else{
          targetInView = targetInView.concat("False");
        }
        var batteryState = "Battery: ";
        var percent = this.state.phonebook[key];
        if (typeof percent === 'string'){
          batteryState = batteryState.concat(this.state.phonebook[key]);
        }
        else{
          batteryState = batteryState.concat(this.state.phonebook[key].toFixed(2));
          batteryState = batteryState.concat("%");
        }

        var newRow = [{id: batteryState}, {id: pointing}, {id: targetInView}];
        var tempRow = this.state.rowData;
        tempRow[key] = newRow;
        this.setState({rowData: tempRow});


        var headerIntro = "Status: "
        //time difference in miliseconds
        var timeDifference = 5.;
        var timeDifference = Date.parse(this.state.curTime) - Date.parse(data.data.state[key].last_update_time);
        if (timeDifference <= 60000.){
          headerIntro = headerIntro.concat("Active")
        }
        else{
          headerIntro.concat("Unresponsive...")
        }
        var newHeader = [{header: headerIntro, key: "id"},];
        var tempHeader = this.state.ColumnData;
        tempHeader[key] = newHeader;
        this.setState({ColumnData: tempHeader});
     }
     catch {
        var a = 5;
     }
   }

   updateTime(data){
     this.setState({curTime: data.time});
   }

   dashboardPress(event) {
     this.setState({selectedRow: event.selectedItem.id,});
    }

   render() {
     return (
       <div>
        <Dropdown
          ariaLabel="Dropdown"
          id="object-selection-dropdown"
          items={this.state.dropdownItems}
          label="Select Satellite, Ground Station, or IOT Sensor"
          onChange={(e) => this.dashboardPress(e)}
        />
        <DataTable
          rows={this.state.rowData[this.state.selectedRow]}
          headers={this.state.ColumnData[this.state.selectedRow]}
          render={({ rows, headers, getHeaderProps }) => (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  {headers.map(header => (
                    <TableHeader {...getHeaderProps({ header })}>
                      {header.header}
                    </TableHeader>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map(row => (
                  <TableRow key={row.id}>
                    {row.cells.map(cell => (
                      <TableCell key={cell.id}>{cell.value}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>)}
          />
       </div>
     )
   }
 }

 export default TabledObjects
