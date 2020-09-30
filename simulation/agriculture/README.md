## Agriculture service

Agriculture service contains simple precision agriculture use-case where IOT sensors on farms would send up data about soil moisture, temperature, and more.

This service receives messages from the data service, as input from other nodes, and then outputs it back to the data service, for output to other nodes. There is currently no processing being done on the agricultural data, however this is where future data processing would occur and could be added.

### Callbacks

| **Function Name** | Purpose                                                                                                                                                        |
|-------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **process_data**  | Receives IOT data packets from the data service, processes them (currently not doing any processing), and then sends processed data back to the data service.  |
