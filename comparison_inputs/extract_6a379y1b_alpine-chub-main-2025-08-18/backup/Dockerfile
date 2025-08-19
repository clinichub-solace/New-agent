FROM alpine:latest

# Install required packages
RUN apk add --no-cache \
    restic \
    mongodb-tools \
    curl \
    bash \
    dcron \
    tzdata

# Create backup user
RUN addgroup -g 1000 backup && \
    adduser -u 1000 -G backup -s /bin/bash -D backup

# Copy backup scripts
COPY backup.sh /usr/local/bin/backup.sh
COPY restore.sh /usr/local/bin/restore.sh

# Set permissions
RUN chmod +x /usr/local/bin/backup.sh /usr/local/bin/restore.sh

# Create directories
RUN mkdir -p /backup /logs && \
    chown -R backup:backup /backup /logs

# Switch to backup user
USER backup

# Set working directory
WORKDIR /backup

# Health check
HEALTHCHECK --interval=300s --timeout=30s --start-period=60s --retries=3 \
    CMD restic check --read-data-subset=1% || exit 1

# Start cron daemon and keep container running
CMD ["sh", "-c", "crond -f -d 8"]