# Dev-mode container for the Vite dashboard.
# Code is bind-mounted via docker-compose; this image only provides Node + deps.
FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
