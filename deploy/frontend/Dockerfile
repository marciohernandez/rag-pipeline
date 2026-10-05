# syntax=docker/dockerfile:1.7

FROM node:24-slim AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

FROM node:24-slim AS build
ENV NEXT_TELEMETRY_DISABLED=1
ARG API_PROXY_TARGET
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
RUN test -n "$API_PROXY_TARGET" \
    && API_PROXY_TARGET="$API_PROXY_TARGET" npm run build

FROM node:24-slim AS runtime
ENV HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3000
WORKDIR /app

COPY --from=build --chown=node:node /app/public ./public
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static

USER node

EXPOSE 3000

CMD ["node", "server.js"]
