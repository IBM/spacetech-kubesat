## Orbit Service

The main purpose of the orbit service is to provide all of the satellite services with up to date information about the current picture of all the nodes.

Orbit service utilizes the orekit library to do all of the orbital mechanics. This service receives state messages and keeps track of the location, trajectory, and pose of every satellite in the swarm as accurately as possible under imposed restrictions.

Orbits service runs on each satellite propagating orbits and attitudes for all other satellites and updating with new information when in range. Simulates attitude (pointing) of each satellite, with flexibility for tracking other satellites and terrestrial targets enabled by the custom functions extending Orekit found in the kubesat-utils repository.

It also receives messages from the reinforcement learning service, and changes the satellite mode between sending or receiving data as well as telling the satellite what to point at.

### Callbacks
| **Function Name**                  | Purpose                                                                                                             |
|------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| **cubesat_state**                  | Update the state of a cubesat in the shared dictionary                                                              |
| **cubesat_X_attitude_provider**    | Update the attitude law for a satellite (satellite ID given in the subject of the message) in the shared dictionary |
| **simulation_timepulse_propagate** | Propagates the satellites current orbit and attitude                                                                |
| **cubesat_X_point_to_cubesat_Y**   | Updates Attitude Law to point to a specific satellite given its orbit parameters                                    |
| **update_transmission_mode**       | Updates the current transmission mode of the satellite (sending or receiving)                                       |
