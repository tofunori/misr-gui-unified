# Multi-stage Dockerfile for MISR GUI
# Stage 1: Python 3.6 environment for MISR Toolkit
FROM continuumio/miniconda3:4.10.3 AS misr-toolkit-env

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libhdf4-dev \
    libhdf5-dev \
    libnetcdf-dev \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Create Python 3.6 environment
RUN conda create -n misr-toolkit-py36 python=3.6 -y
SHELL ["conda", "run", "-n", "misr-toolkit-py36", "/bin/bash", "-c"]

# Install MISR Toolkit dependencies
RUN conda install -y -c conda-forge \
    numpy=1.19.5 \
    gdal=3.2.3 \
    hdf4=4.2.15 \
    netcdf4=1.5.8

# Install MISR Toolkit
# Note: This assumes you have access to MISR Toolkit installation files
# You may need to adjust this based on your MISR Toolkit source
COPY misr_toolkit_installation/ /tmp/misr_toolkit/
RUN cd /tmp/misr_toolkit && python setup.py install

# Stage 2: Main application environment (Python 3.12)
FROM continuumio/miniconda3:latest AS main-app

# Install system dependencies for GUI
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
    && rm -rf /var/lib/apt/lists/*

# Create main application environment
RUN conda create -n misr-gui python=3.12 -y
SHELL ["conda", "run", "-n", "misr-gui", "/bin/bash", "-c"]

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy MISR Toolkit environment from stage 1
COPY --from=misr-toolkit-env /opt/conda/envs/misr-toolkit-py36 /opt/conda/envs/misr-toolkit-py36

# Copy application code
COPY . /app/
WORKDIR /app

# Set environment variables
ENV DISPLAY=:99
ENV PYTHONPATH=/app

# Create entrypoint script
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
# Start virtual display for GUI
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99

# Wait for display to be ready
sleep 2

# Activate main environment and run application
conda run -n misr-gui python main.py
EOF

RUN chmod +x /app/entrypoint.sh

# Expose port if needed (for remote access)
EXPOSE 5900

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]