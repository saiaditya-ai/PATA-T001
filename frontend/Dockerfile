FROM node:18-alpine

WORKDIR /app

COPY package.json ./
# We copy package.json first. Since we might not have a package-lock.json initially, 
# we allow npm install to run without failing.
RUN npm install

COPY . .

EXPOSE 5173

# Run the Vite development server so hot-reloading works
CMD ["npm", "run", "dev", "--", "--host"]
