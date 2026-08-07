FROM python:3.11-slim

# Install system dependencies required for libpostal and building Python packages
RUN apt-get update && apt-get install -y \
    curl \
    autoconf \
    automake \
    libtool \
    pkg-config \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone and install libpostal from source
# NOTE: This step will download ~2GB of machine learning training data during configuration
RUN git clone https://github.com/openvenues/libpostal /opt/libpostal \
    && cd /opt/libpostal \
    && ./bootstrap.sh \
    && ./configure --datadir=/opt/libpostal_data \
    && make -j$(nproc) \
    && make install \
    && ldconfig

# Set up the Python application
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
