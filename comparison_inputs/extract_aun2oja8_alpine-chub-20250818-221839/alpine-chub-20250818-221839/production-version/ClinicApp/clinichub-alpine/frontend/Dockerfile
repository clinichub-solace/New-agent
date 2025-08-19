FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

RUN addgroup -g 1000 clinichub && \
    adduser -D -s /bin/sh -u 1000 -G clinichub clinichub && \
    chown -R clinichub:clinichub /app

USER clinichub
EXPOSE 3000

CMD ["npm", "start"]
