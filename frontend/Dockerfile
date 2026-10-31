# ==============================================================================
# NIRMAYA Next.js 15 Frontend - Multi-Stage Production Alpine Dockerfile
#
# Standards & Compliance:
# - Base: node:20-alpine (Minimal attack surface footprint < 150MB)
# - Security: CIS Docker Benchmark (Non-root user nextjs UID 1001, GID 1001)
# - Output: Next.js 15 standalone server traced bundling
# - Healthcheck: Native OCI HTTP probe targeting /api/health
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependencies Resolution (deps)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package manifests for deterministic dependency installation
COPY package.json package-lock.json ./
RUN npm ci

# ------------------------------------------------------------------------------
# Stage 2: Next.js Standalone Build (builder)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

# Inherit pre-installed dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Disable telemetry and set production build environment
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Compile standalone traced server bundle and static chunks
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 3: Stripped Production Runner (runner)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Install curl for container orchestration health checks
RUN apk add --no-cache curl

# Enforce CIS Docker Benchmark 4.1: Unprivileged system user nextjs (UID 1001)
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy static assets and public assets
COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
RUN mkdir .next && chown nextjs:nodejs .next
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root execution context
USER nextjs

EXPOSE 3000

# Native OCI container health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1

# Launch Next.js standalone server
CMD ["node", "server.js"]

