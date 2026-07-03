FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Vite requires explicit host definition to bind properly inside a container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
