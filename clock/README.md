## Clock Service
Clock sends out the timestep messages on a regular interval on a single NATS channel. Almost all of the other services are subscribed to that channel.

This service simulates master timing of the simulation on which all calculations, visualizations, and communcations are based on. Broadcasts a timestep message that all of the other services can subscribe to in order to keep the simulation synchronized.

Changing the simulation schedule callback period will change the ratio of real time to simulated time passing. The value in the schedule callback is the time in seconds of how frequently a timestep message is sent out. The time change between the timestep messages as well as the initial time can be set in the clock config file.

| **Function Name** | Purpose                                                                                                     |
|-------------------|-------------------------------------------------------------------------------------------------------------|
| **send_timestep** | Broadcast the current time of the simulation and updates it by the timestep interval defined in the config. |
