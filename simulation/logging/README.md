## Logging Repository
Log collector for all messaging between satellites, groundsations, and IOT ground sensors.

Logging logs all errors inside callback functions of all of the microservices as well as deliberate messages that are sent to the logger. The logging services prints these events/messages to a logging file. Any other microservice can send a message to the logging service.
