## Cesium Graphing Service
CZML is the graphics service that provides visualization for the dashboard. This service receives timestep messages, and each timestep updates the visualization. It also receives state messages, describing the state of each satellite, from the orbit microservice of each satellite node.

Code relating to Cesium 3D visualization on user interface sends descriptive CZML (JSON) packets via NATS to the dashboard for state visualization. Enables visualization of satellite positions and orbits, ground and IoT station locations, and transmission links when any pair is in range. Transmission frequency may be tuned according to the user's wishes.

Detailed documentation of CZML can be found [here](https://github.com/AnalyticalGraphicsInc/czml-writer/wiki/CZML-Guide)

### Callbacks

| **Function Name**             | Purpose                                                                                                                                        |
|-------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| **cubesat_state**             | Update the state of a cubesat in the shared dictionary                                                                                         |
| **send_visualization_packet** | Send packets over NATS describing the state of the swarm. Packets set include ground stations, satellites, and links when pairs  are in range. |
