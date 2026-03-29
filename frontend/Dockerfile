# syntax=docker/dockerfile:1.7
FROM node:24-alpine

WORKDIR /workspace
RUN corepack enable

COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY frontend/package.json frontend/package.json

COPY frontend ./frontend
RUN pnpm install --filter frontend --frozen-lockfile
WORKDIR /workspace/frontend

EXPOSE 3000
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "3000"]
