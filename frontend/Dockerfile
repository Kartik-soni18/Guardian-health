# ==========================================
# Stage 1: Build — Node.js build environment
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /build

# Install dependencies (cache layer)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline --no-audit

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Serve — nginx with SPA config
# ==========================================
FROM nginx:alpine AS runtime

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/guardian.conf

# Copy built static assets from builder
COPY --from=builder /build/dist /usr/share/nginx/html

# Security: run nginx as non-root (optional enhancement)
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Expose HTTP port
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
