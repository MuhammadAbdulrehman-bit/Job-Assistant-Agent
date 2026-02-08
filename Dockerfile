# Use the same python version your brother used
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (for better caching)
COPY requirement.txt .

# Install dependencies
# We add --no-cache-dir to keep the image small
RUN pip install --no-cache-dir -r requirement.txt

# Copy the rest of the application code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# The command to start the application
# We use the array format for safety
CMD ["streamlit", "run", "src/Dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
