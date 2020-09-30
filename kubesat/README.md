# KubeSat

KubeSat package provides Redis, NATs, and Kubernetes wrappers. Users can use and extend the library to develop and deploy resource managers and services. Its main components are:

## Base Service
The base service underneath every microservice. Holds state variables and contains decorators for the NATS callbacks.

## Message
The message class that every Nats messages takes the form of. Has a sender id for who is sending the message, an origin id for who created the message, and a data field.

## Nats Handler/Nats Logger
Custom Nats client for the Nats.io messaging service. Implements publish, subscribe, request, reply and logging.

## Redis Handler
Added functionality to preexisting Redis python client. Get and setting data in a Redis server in a dictionary form.

## Kubernetes Handler
Provides core and batch API client functions to manage Kubernetes resources and jobs.

## Validation
Contains JSON schemas to validate that messages and the shared storage are all of the proper form. Also contains decorators to validate that nodes are in range and thus able to communicate.
