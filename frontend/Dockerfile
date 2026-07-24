FROM node:20.20.1-bookworm-slim

WORKDIR /app

# Native bindings (SWC, lightningcss) require glibc — avoid Alpine/musl here.
COPY package.json package-lock.json ./
RUN npm ci

COPY docker-entrypoint.dev.sh /usr/local/bin/docker-entrypoint.dev.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.dev.sh

COPY . .

EXPOSE 3000

ENTRYPOINT ["docker-entrypoint.dev.sh"]
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]


