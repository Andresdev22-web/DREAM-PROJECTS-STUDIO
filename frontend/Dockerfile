
# Etapa de construcción
FROM node:lts-alpine AS build

WORKDIR /app

RUN apk add --no-cache git

# Activar Corepack para gestionar pnpm
RUN corepack enable

# Copiar los archivos de dependencias
COPY package.json pnpm-lock.yaml ./

# Instalar exactamente las dependencias del lockfile
RUN pnpm install --frozen-lockfile

# Copiar el código del proyecto
COPY . .

# Construir Astro
RUN pnpm run build

# Etapa de producción
FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
