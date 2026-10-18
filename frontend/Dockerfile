# Etapa de construcción
FROM node:lts-alpine AS build

WORKDIR /app

# Instalar Git para las dependencias de GitHub
RUN apk add --no-cache git

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Etapa de producción
FROM nginx:stable-alpine

# Copiar los archivos generados por Astro
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
