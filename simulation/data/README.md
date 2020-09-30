## Data Service

Data service handle data exchange between the internal satellite services and the other nodes (satellites, groundstations, and IoT sensors).

This service has multiple functions. Under the default precision agriculture use case, it receives agricultural data from the IOT sensors, and then forwards that data to the satellite's internal agriculture service.

It also receives data messages from inside of the satellite and puts those data messages into the buffer, to later be sent out. It then sends messages from the data buffer when it is in sending mode. These messages it sends out includes both the agricultural data messages that have been processed within the satellite, as well as battery data.

The data service also receives messages from the orbit services of the other satellites, in order to understand whether it is able to physically communicate with those satellites or not. It also receives messages from it's own orbit service in order to determine whether it can physically communicate with the other nodes.
