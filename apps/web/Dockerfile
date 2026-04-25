# [INPUT]: Vite React frontend source tree and npm dependencies
# [OUTPUT]: Local relay-web image with a Vite dev server
# [POS]: Container build definition for single-node local deployment
# [PROTOCOL]:
#   1. Keep the image focused on local web management only.
#   2. Runtime/API endpoint changes must be reflected in README and compose docs.

FROM node:20-slim

WORKDIR /app

COPY apps/web/package*.json ./
RUN npm install

COPY apps/web /app

EXPOSE 5173

CMD ["sh", "-c", "npm ci && npm run dev -- --host 0.0.0.0 --port 5173"]
