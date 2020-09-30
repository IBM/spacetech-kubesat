
### Utils
Underlying utilites including [OreKit](https://www.orekit.org), Redis, and NATs wrappers. See API in official documentation for individual modules including orbital mechanics functions. Test files include additional examples of functionality and input options.  

### Base Simulation
The base simulation underneath every microservice. Holds state variables and contains decorators for the NATS callbacks.

### Initiate
Gets some data necessary to run orekit

### Message
The message class that every Nats messages takes the form of. Has a sender id for who is sending the message, an origin id for who created the message, and a data field.

### Nats Handler/Nats Logger
Custom Nats client for the Nats.io messaging service. Implements publish, subscribe, request, reply and logging.

### Orekit
Custom python wrapper with added functionality for the orbital mechanics toolkit Orekit. Contains functions to propagate orbits, change attitude to point at targets, calculate field of view, convert different data types, and other helpers.

### Redis Handler
Added functionality to preexisting Redis python client. Get and setting data in a Redis server in a dictionary form.

### Services
Map of services.

### Testing
Contains mock versions of our custom objects and classes to use in unit tests.

### Validation
Contains JSON schemas to validate that messages and the shared storage are all of the proper form. Also contains decorators to validate that nodes are in range and thus able to communicate.
