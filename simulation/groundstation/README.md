## Ground Station Service

Groundstation service receives agricultural data and telemetry data from the satellites that are pointing at it and sending data to it. It also communicates the number of packets received to the RL service so the RL service can calculate the reward. The groundstation service receives messages from the orbit service of the passing satellites in order to know what is pointing at it. The groundstation also receives the phonebooks from passing satellites, and sends cluster messages to the cluster service in order to tell cubesats to cluster.

### Callbacks

| **Function Name**        | Purpose                                                                                                                                           |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **receive_data**         | Receives a data packet, updates the number of received packets, requests more data, and notifies the logger that it has received data             |
| **update_pointing_list** | Receives state messages from passing satellites and uses those to update the internal list of satellites currently pointing at this groundstation |
| **update_cluster**       | Checks the phonebook and sends a clustering command if two satellites are in range                                                                |
| **update_sat_ip**        | Recieves and stores the ip address of a satellite in shared_storage     
