FROM node:20-alpine

WORKDIR /app/whatsapp_service

COPY package.json ./
RUN npm install --omit=dev

COPY server.js silenciar_logs.js ./

ENV BAILEYS_SERVICE_HOST=0.0.0.0 \
    BAILEYS_SERVICE_PORT=3001 \
    BAILEYS_AUTH_DIR=/data/auth_info

RUN mkdir -p /data/auth_info

EXPOSE 3001

CMD ["npm", "start"]
