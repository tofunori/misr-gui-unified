# MISR GUI with MISR Toolkit - Docker Container
FROM ubuntu:20.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies in stages to avoid conflicts
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    build-essential \
    cmake \
    wget \
    curl \
    pkg-config \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    # GUI dependencies for X11 forwarding
    python3-tk \
    xauth \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Install HDF and geospatial libraries separately to avoid conflicts
RUN apt-get update && apt-get install -y \
    libhdf4-alt-dev \
    libhdf5-dev \
    libnetcdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Install GDAL and spatial libraries
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Install Python dependencies first
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install additional dependencies that might be needed
RUN pip3 install --no-cache-dir \
    numpy \
    scipy \
    matplotlib \
    pillow \
    xarray \
    netcdf4 \
    h5py \
    rasterio \
    rioxarray \
    geopandas \
    fiona \
    shapely \
    pyproj

# Install MISR Toolkit
RUN pip3 install --no-cache-dir MisrToolkit

# Alternative: Build MISR Toolkit from source if pip fails
# RUN git clone https://github.com/nasa/MISR-Toolkit.git /tmp/misr-toolkit && \
#     cd /tmp/misr-toolkit && \
#     mkdir build && cd build && \
#     cmake .. && \
#     make && make install && \
#     cd /tmp && rm -rf misr-toolkit

# Copy the application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Create a non-root user for security
RUN useradd -m -s /bin/bash misruser && \
    chown -R misruser:misruser /app
USER misruser

# Set display for GUI applications
ENV DISPLAY=:0

# Expose any ports if needed (none for this GUI app)
# EXPOSE 8080

# Create startup script
RUN echo '#!/bin/bash\n\
echo "MISR GUI Docker Container"\n\
echo "========================"\n\
echo "Available processing modes:"\n\
echo "✅ NetCDF Processing (Advanced)"\n\
echo "✅ HDF Processing (MISR Toolkit)"\n\
echo ""\n\
echo "Starting MISR GUI..."\n\
python3 main.py' > /app/start_gui.sh && \
chmod +x /app/start_gui.sh

# Default command
CMD ["/app/start_gui.sh"]