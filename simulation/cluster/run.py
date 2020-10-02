# Copyright 2020 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
from cluster_service import simulation

def clean(stri):
    stri = stri.strip(" ")
    stri = stri.strip("\n")
    stri = stri.strip("\r")
    stri = stri.strip("\t")
    return stri

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--nats_user', help='Username for the NATS connection')
    parser.add_argument('-p', '--nats_password', help='Password for the NATS connection')
    parser.add_argument('-s', '--nats_host', help='Port for the NATS connect')
    parser.add_argument('-r', '--redis_password', help='Password for the Redis connection')
    parser.add_argument('-d', '--redis_host', help='Host for the Redis connection')
    parser.add_argument('-a', '--api_host', help='Hostname for the API')
    parser.add_argument('-t', '--api_port', help='Port for the API')
    args = parser.parse_args()

    print(f"Nats user: {args.nats_user}")
    print(f"Nats password: {args.nats_password}")
    print(f"Redis password: {args.redis_password}")
    print(f"Api host: {args.api_host}")
    print(f"Api port: {args.api_port}")

    arguments = {}

    if args.nats_user:
        arguments["nats_user"] = clean(args.nats_user)
    if args.nats_password:
        arguments["nats_password"] = clean(args.nats_password)
    if args.nats_host:
        arguments["nats_host"] = clean(args.nats_host)
    if args.redis_password:
        arguments["redis_password"]  = clean(args.redis_password)
    if args.redis_host:
        arguments["redis_host"] = clean(args.redis_host)
    if args.api_host:
        arguments["api_host"] = clean(args.api_host)
    if args.api_port:
        arguments["api_port"] = int(clean(args.api_port))

    simulation.run(**arguments)