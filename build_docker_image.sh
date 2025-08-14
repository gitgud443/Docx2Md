#!/bin/bash
# File: build_docker_image.sh

# Build the Docker image for image conversion
docker build -t tech-doc-image-converter -f Dockerfile.image-converter .

echo "Docker image 'tech-doc-image-converter' built successfully!"
