FROM python:3.14-slim

# https://raw.githubusercontent.com/upciti/wakemeops/main/assets/install_repository
COPY wakemeops-keyring.asc /etc/apt/keyrings/wakemeops-keyring.asc
RUN cat <<'EOF' >/etc/apt/sources.list.d/wakemeops.sources
Components: dev devops secops terminal desktop
Enabled: yes
X-Repolib-Name: wakemeops
Signed-By: /etc/apt/keyrings/wakemeops-keyring.asc
Suites: stable
Types: deb
URIs: http://deb.wakemeops.com/wakemeops/
EOF

# Install system dependencies once
RUN apt-get update && apt-get install -y \
    git git-crypt \
    openssh-client \
    rsync \
    make \
    bind9-dnsutils \
    jq

RUN apt-get install -y \
    default-libmysqlclient-dev \
	python3-cairo

# install uv from wakemeops repo:
RUN apt-get install -y \
    uv

RUN rm -rf /var/lib/apt/lists/*

# Install Python tooling once
RUN pip install --upgrade pip
RUN pip install --no-cache-dir uv

# Set the working directory
WORKDIR /app

COPY uv.lock ./
COPY pyproject.toml ./
COPY README.md ./

RUN uv sync
