FROM node:24-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig.json ./
COPY src ./src
COPY tests ./tests
RUN npm test

FROM node:24-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY --from=build /app/dist/src ./dist/src

USER node

CMD ["node", "dist/src/main.js"]
