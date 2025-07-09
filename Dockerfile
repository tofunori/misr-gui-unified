# Dockerfile for MISR GUI
FROM continuumio/miniconda3:latest

# Install system dependencies for GUI and MISR Toolkit
RUN apt-get update && apt-get install -y \
    python3-tk \
    xvfb \
    x11-apps \
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    libxtst6 \
    libxi6 \
    libgconf-2-4 \
    gcc \
    g++ \
    libhdf4-dev \
    libhdf5-dev \
    libnetcdf-dev \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Create main application environment (Python 3.12)
RUN conda create -n misr-gui python=3.12 -y

# Create Python 3.6 environment for MISR Toolkit
RUN conda create -n misr-toolkit-py36 python=3.6 -y

# Install MISR Toolkit dependencies in Python 3.6 environment
RUN conda install -n misr-toolkit-py36 -y -c conda-forge \
    numpy=1.19.5 \
    gdal=3.2.3 \
    hdf4=4.2.15 \
    netcdf4=1.5.8

# Switch to main environment for application dependencies
SHELL ["conda", "run", "-n", "misr-gui", "/bin/bash", "-c"]

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Note: MISR Toolkit installation requires manual setup
# See README_DOCKER.md for instructions

# Copy application code
COPY . /app/
WORKDIR /app

# Set environment variables
ENV DISPLAY=:99
ENV PYTHONPATH=/app

# Create entrypoint script
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo '# Start virtual display for GUI' >> /app/entrypoint.sh && \
    echo 'Xvfb :99 -screen 0 1024x768x24 &' >> /app/entrypoint.sh && \
    echo 'export DISPLAY=:99' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Wait for display to be ready' >> /app/entrypoint.sh && \
    echo 'sleep 2' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Activate main environment and run application' >> /app/entrypoint.sh && \
    echo 'conda run -n misr-gui python main.py' >> /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Expose port if needed (for remote access)
EXPOSE 5900

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]