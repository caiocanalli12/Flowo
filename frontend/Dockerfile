# Debian (glibc): os binários nativos do Vite 8/rolldown não dependem de musl.
FROM node:24-slim

WORKDIR /app

# Dependências primeiro, para que mudanças no código não invalidem esta camada.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
