# NOTE: Some cloud providers will require you to specify the platform to match your target architecture
# i.e.: AWS Lightsail requires arm64, therefore you update your FROM statement to: FROM --platform=linux/arm64 motiadev/motia:latest
FROM motiadev/motia:latest

# Install Dependencies
COPY package*.json ./
RUN npm ci --only=production

# Move application files
COPY . .

# Setup python steps dependencies (REQUIRED for Python steps)
RUN npx motia@latest install

# Expose outside access to the motia project
EXPOSE 3000

# Run your application
CMD ["npm", "run", "start"]