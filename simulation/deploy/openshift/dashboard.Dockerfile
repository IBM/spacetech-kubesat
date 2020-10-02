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

FROM node:alpine as build-deps
WORKDIR /usr/src/app
RUN apk update && apk --no-cache add git
RUN cd /tmp && git clone https://github.com/IBM/spacetech-kubesat --branch master --single-branch
RUN mv /tmp/spacetech-kubesat/dashboard/* /usr/src/app/

FROM node:alpine
WORKDIR /usr/src/app
COPY --from=build-deps /usr/src/app/build /usr/src/app/build
COPY --from=build-deps /usr/src/app/app.js /usr/src/app
COPY --from=build-deps /usr/src/app/server_package.json /usr/src/app
RUN mv server_package.json package.json \
    && npm install
EXPOSE 8080
CMD ["node", "app.js"]
