# <img src="assets/IBMSpaceTechStarLogo.png" width="900">
# 🛰️ KubeSat 🛰️
IBM SpaceTech KubeSat is an open source project for building a cognitive, autonomous framework for satellite constellations and swarms. KubeSat allows for the simulation and optimization of multi-satellite communications.

This project simulates accurate orbital mechanics for each object via [OreKit](https://www.orekit.org); uses these calculations to place restrictions on communications between satellites, groundstation, and ground sensors; incorporates [NATS.io](https://nats.io) messaging services; and publishes these communications for visualization on a web dashboard built using Cesium and Carbon.

## Overview
KubeSat consists of a combination of microservices that interact with each other using NATS messaging. These services are distributed between Satellite and Groundstation nodes, and are grouped into three categories - Simulation, Satellite, and IoT/Ground station.

Simulation services include clock, config, logging, czml, dashboard, and cluster. IoT/Groundstation services include iot and groundstation services. Satellite services include orbits, data, reinforcement learning, RL training. Agriculture is the application use-case with associated service named agriculture running on each satellite node.

A template service is provided as a starting point to write new services and additional utility libraries.  

#### Utilities
* [Utils](utils)
* [Template Service](template)

#### Simulation
* [Clock](clock)
* [Cluster](cluster)
* [Config](config)
* [CZML](czml)
* [Logging](logging)
* [Dashboard](https://github.com/IBM/spacetech-kubesat/dashboard)

#### Satellite
* [Agriculture](agriculture)
* [Data](data)
* [Orbits](orbits)
* [Reinforcement Learning](rl)
* [Reinforcement Learning Training Agent](rl-training)

#### IoT & Ground
* [Ground](ground)
* [IoT](iot)

### Technical Architecture
KubeSat technical architecture is available [here](https://ibm-kubesat.gitbook.io/kubesat/project-architecture/overview)

### Getting Started
Setup development environment bootstrapped in a docker container.

### Pre-requisite
Docker should be installed and running on your machine.

### Instructions

By default, code from `master` branch will be cloned to `/tmp/spacetech-kubesat` folder on your machine.
```bash
curl -sSL https://raw.githubusercontent.com/IBM/spacetech-kubesat/master/devtest/bootstrap.sh | sh
```

Use following commands to bootstrap your devtest environment with custom options.

- Pull code from a specific branch
```
curl -sSL https://raw.githubusercontent.com/IBM/spacetech-kubesat/master/devtest/bootstrap.sh | sh -s -- -b <branch-name>
```
- Clone git repo to a specific folder
```
curl -sSL https://raw.githubusercontent.com/IBM/spacetech-kubesat/master/devtest/bootstrap.sh | sh -s -- -r <folder-name>
```

Post-bootstrap, all kubesat services are running with dashboard at http://localhost:8080

Logs for each service can be found in `devtest` folder.

After making any code changes, run `docker exec -it dev-kubesat bash run.sh` to reload kubesat services with code updates.


### Helpful Links
* [Documentation](https://ibm-kubesat.gitbook.io/kubesat/)
* [Personalize KubeSat](https://ibm-kubesat.gitbook.io/kubesat/personalize-to-your-use-case)


### Maintainers

* Moritz Stephan ([GitHub](https://github.com/austrian-code-wizard) | [LinkedIn](https://www.linkedin.com/in/moritz-stephan))
* Flynn Dreilinger ([Github](https://github.com/polygnomial) | [LinkedIn](https://www.linkedin.com/in/flynnd))
* Ian Chang ([GitHub](https://github.com/iannchang) | [LinkedIn](https://www.linkedin.com/in/ianchang2000/))
* Grant Regen ([GitHub](https://github.com/grantregen) | [LinkedIn](https://www.linkedin.com/in/grant-regen))
* Jesus Meza ([GitHub](https://github.com/jemeza) | [LinkedIn](https://www.linkedin.com/in/jesusmero/))
