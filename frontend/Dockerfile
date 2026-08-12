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

ARG NEXT_PUBLIC_API_URL=https://nutrimind-ai-yrgw.onrender.com/api/v1
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npx next build

FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["npx", "next", "start", "-h", "0.0.0.0", "-p", "3000"]
