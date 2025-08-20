#!/bin/bash
# File: build_docker_image.sh

# Build the Docker image for image conversion
docker build \
  --build-arg http_proxy=http://10.253.52.118/ \
  --build-arg https_proxy=http://10.253.52.118/ \
  --build-arg no_proxy=localhost,127.0.0.1,10.253.52.118 \
  --build-arg NEXUS_LOGIN=arobin \
  --build-arg NEXUS_PASSWORD='R_5525$3698nuar' \
  -t tech-doc-image-converter \
  -f Dockerfile.image-converter .

echo "Docker image 'tech-doc-image-converter' built successfully!"
