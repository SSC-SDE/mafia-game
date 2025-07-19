# Frontend Dockerfile (multi-stage)
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .
RUN npm run build

# Use lightweight Nginx to serve static files
FROM nginx:alpine


# Copy build output from previous stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Optional: Add custom nginx config if needed
# COPY nginx.conf /etc/nginx/nginx.conf
