## Configuration Service

Config service initializes all of the other microservices. This service pulls the configuration dictionaries from the configuration json files and sends the initial configuration dictionaries (shared_storage) to other services when requested. It also checks the status of all of the services every 10 seconds and keeps track of whether they are running or not.

Each unique microservice needs its own configuration file. This configuration file contains information about each service, like it's sender id and port, as well as a shared storage dictionary that is actually accessible by the service's callback functions.  

The config shared storage dictionary contains a dictionary of the wanted services of the desired number of nodes. For example, the satellites section of the file would contain a dictionary where the keys are the id's of the desired satellites and the values are the services and a boolean value that tells whether the service currently running or not.

### Callbacks

| **Function Name**      | Purpose                                                                                                                                                                                                                        |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **initialize_service** | Initializes services based on given config files. Pulls the dictonaries from the config files then receives a request from a service when it is created, and based off of the given service type returns a config dictionary.  |
| **check_status**       | Every 10 seconds sends a Nats request to every service that in its shared storage is "true" (ie: running) and then if there is no reply changes the service status to false (ie: not running).                                 |

### Config Files Structure

The simulation_config folder contains the json files which contain the initial configuration data for the services.
The simulation_config folder should contain four subfolders: simulation, cubesats, groundstations, and iots. Cubesats should contain a folder for each satellite that is to be simulated. Each satellite folder should be labelled as the satellite id, and contain the configuration files for the agriculture, data, orbits, rl, and rl_training. The phonebooks in these services must be initialized with all of the nodes inside of them. In addition, all of the configuration files in each of the individual cubesat folders should share the same sender id. Groundstations should contain a folder for each groundstation that is to be simulated. Each groundstation folder should contain a configuration file for the groundstation service. Iots should contain a folder for each iot that is to be simulated. Each iot folder should contain a configuration file for the iot service. Each groundstation and iot service configuration must have a unique sender id. Simulation should contain the json configuration files for clock, logging, czml, and config. Config should contain a dictionary that has all of the cubesats, groundstations, and iots that are to be initialized and their subservices. Each service should have an associated boolean value that should initally be set to false. If you are confused about the structure of an invidual config file, look at the shared storage schemas in the validation utils.
