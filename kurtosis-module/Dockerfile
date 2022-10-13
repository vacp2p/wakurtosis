# ============================ Base ============================
FROM alpine:3.15 AS base

# Unfortunately Alpine packages are updated in-place, and old versions are discarded so there's no way to use older versions and pin the NodeJS version
RUN apk add --no-cache nodejs-current
WORKDIR /build

COPY package.json .
COPY yarn.lock .

# ============================ Build ============================
FROM base AS build

RUN apk add --no-cache yarn

# Install production packages
RUN yarn install --frozen-lockfile --production=true

# Use node-prune to further reduce unnecessary files: https://github.com/tj/node-prune
RUN curl -sf https://gobinaries.com/tj/node-prune | sh

# Set aside these production dependencies for use later
RUN cp -R node_modules prod_node_modules

# Now install ALL node_modules, including 'devDependencies'
RUN yarn install --frozen-lockfile

COPY . .

# Run tests & compile
RUN yarn build

#
# ============================ Run ============================
FROM base AS run
WORKDIR /run

# copy production node_modules
COPY --from=build /build/prod_node_modules ./node_modules
# copy app sources
COPY --from=build /build/build ./build

CMD node build/main.js

