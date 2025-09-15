# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Set memory limits and increase timeouts
ENV NODE_OPTIONS="--max_old_space_size=2048"
ENV CI=false
ENV GENERATE_SOURCEMAP=false

# Copy package files
COPY package.json package-lock.json ./

# Clear npm cache and install dependencies with specific settings
RUN npm cache clean --force && \
    npm ci --no-audit --no-fund --timeout=300000

# Copy source code
COPY . .

# Build the app with verbose logging
RUN npm run build --verbose

# Production stage
FROM nginx:alpine

# Copy build files to nginx
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]