FROM node:18-alpine

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache python3 make g++ curl

# Copy package files
COPY package*.json ./

# Remove package-lock.json to avoid conflicts with yarn
RUN rm -f package-lock.json

# Install dependencies using yarn
RUN yarn install --frozen-lockfile || yarn install

# Copy application code
COPY . .

# Build the application for production
RUN yarn build

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["yarn", "start"]