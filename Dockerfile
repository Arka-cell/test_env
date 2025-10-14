FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy app files and templates
COPY app.py .
COPY templates ./templates


# Expose port 9998
EXPOSE 9998

# Run the app on port 9998
CMD ["python", "app.py"]
