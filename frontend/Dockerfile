FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
<<<<<<< HEAD
RUN npm install
=======
RUN npm install --legacy-peer-deps
>>>>>>> af556fbec9d17c51b31bacd7570f180a38803fdc

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
