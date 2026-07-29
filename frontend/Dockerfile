FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig.json next.config.ts postcss.config.mjs tailwind.config.ts eslint.config.mjs ./
COPY app/ app/
COPY components/ components/
COPY contexts/ contexts/
COPY features/ features/
COPY hooks/ hooks/
COPY lib/ lib/
COPY services/ services/
COPY types/ types/

ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
