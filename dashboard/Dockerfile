FROM node:alpine as build-deps
WORKDIR /usr/src/app
COPY package.json ./
RUN yarn
COPY . ./
RUN yarn build

FROM node:alpine
WORKDIR /usr/src/app
COPY --from=build-deps /usr/src/app/build /usr/src/app/build
COPY --from=build-deps /usr/src/app/app.js /usr/src/app
COPY --from=build-deps /usr/src/app/server_package.json /usr/src/app
RUN mv server_package.json package.json \
    && npm install

EXPOSE 8080
CMD ["node", "app.js"]