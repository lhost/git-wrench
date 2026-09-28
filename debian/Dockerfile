FROM debian:trixie-slim

# Install system dependencies once
RUN apt-get update && apt-get install -y \
      debhelper dh-python python3-all python3-hatchling python3-installer \
      python3-build pybuild-plugin-pyproject build-essential

RUN rm -rf /var/lib/apt/lists/*
