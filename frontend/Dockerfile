# ============================================================================
# Stage 1: Build Static React Assets with Node 20
# ============================================================================
FROM node:20-alpine as builder

WORKDIR /app

# Install dependencies first for efficient layer caching
COPY package*.json /app/
RUN npm ci || npm install

# Copy source code and build config
COPY . /app/

# Build production bundle with Vite
RUN npm run build

# ============================================================================
# Stage 2: Serve Bundle with Nginx Alpine (Cloud Run & Compose Compatible)
# ============================================================================
FROM nginx:alpine as runner

# Remove default nginx html files
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled artifacts from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 8080

# Dynamic port substitution for Cloud Run ($PORT) with fallback to 80
CMD ["/bin/sh", "-c", "sed -i \"s/listen 80;/listen ${PORT:-80};/g\" /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
