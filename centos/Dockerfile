FROM quay.io/centos/centos:stream9

RUN dnf config-manager --set-enabled crb
RUN dnf install -y epel-release
# dnf swap curl-minimal curl
RUN dnf install -y \
        rpm-build \
        git \
        python3-devel \
        python3-pip \
        python3-wheel \
        python3-build \
        python3-installer \
        python3-hatchling \
        python3-pytest \
        make \
        && \
    dnf clean all
