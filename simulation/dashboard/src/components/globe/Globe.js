import React, { Component } from 'react'
import { Viewer, ImageryLayer, CzmlDataSource, CustomDataSource } from "resium";
import { ArcGisMapServerImageryProvider } from "cesium";
import { ContentSwitcher, Switch} from "carbon-components-react";
import { registerOnMessageCallback } from '../../utils/wsConnector'

class Globe extends Component {
  constructor () {
    super();
    this.state = {
      current: [],
      buffer: {},
      document:[]
    };
    registerOnMessageCallback("graphics.sat", (message) => this.updateData.bind(this)(message.data))
    registerOnMessageCallback("graphics.doc", (message) => this.updateDoc.bind(this)(message.data))
    registerOnMessageCallback("graphics.grstn", (message) => this.updateData.bind(this)(message.data))
    registerOnMessageCallback("graphics.iot", (message) => this.updateData.bind(this)(message.data))
    registerOnMessageCallback("graphics.sat2sat", (message) => this.updateData.bind(this)(message.data))
    registerOnMessageCallback("graphics.grstn2sat", (message) => this.updateData.bind(this)(message.data))
  }


  updateData(data) {
    this.state.buffer[data["id"]] = data;
    this.setState({current: this.state.document.concat(Object.values(this.state.buffer))});
    console.log(this.state.current)
  }

  updateDoc(data){
    if(data["id"] == "document"){
      this.setState({
                    document:[data],
                    current:[]
	                  })
    }
  }

  render() {
    return (
      <Viewer
            timeline={false}
            animation={false}
            shouldAnimate={true}
            vrButton={false}
            geocoder={false}
            homeButton={false}
            fullscreenButton={false}
            baseLayerPicker={false}
            infoBox={false}

            navigationHelpButton={false}
            creditContainer={null}
            creditViewport={null}>


            <CzmlDataSource
              data={this.state.current}
              show={true}
            />

      </Viewer>
    )
  }
}

export default Globe
