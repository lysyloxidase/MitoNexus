FROM node:22-alpine

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

RUN corepack enable

WORKDIR /app

COPY package.json pnpm-workspace.yaml ./
COPY apps/frontend/package.json apps/frontend/package.json
COPY packages/shared-types/package.json packages/shared-types/package.json

RUN pnpm install --no-frozen-lockfile

COPY apps/frontend apps/frontend
COPY packages/shared-types packages/shared-types

WORKDIR /app/apps/frontend

EXPOSE 3000

CMD ["pnpm", "dev", "--hostname", "0.0.0.0"]
