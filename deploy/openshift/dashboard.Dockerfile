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
