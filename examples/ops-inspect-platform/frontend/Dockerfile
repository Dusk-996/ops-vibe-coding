# syntax=docker/dockerfile:1.7
# 前端生产镜像（Node 多阶段编译 + 官方非 root Nginx 托管，强制锁死 VITE_USE_MOCK=false）

FROM node:20.18.1-alpine3.20 AS builder

ARG NPM_REGISTRY=https://registry.npmjs.org
ENV VITE_USE_MOCK=false

WORKDIR /build
COPY package.json package-lock.json ./
RUN npm config set registry "${NPM_REGISTRY}" && npm ci --no-audit --no-fund

COPY index.html vite.config.js .env.production ./
COPY src ./src
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27.3-alpine AS runtime

COPY --chown=101:101 nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder --chown=101:101 /build/dist /usr/share/nginx/html

USER 101

EXPOSE 8080
STOPSIGNAL SIGQUIT

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
