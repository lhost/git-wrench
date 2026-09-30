FROM quay.io/centos/centos:stream9

RUN dnf config-manager --set-enabled crb
RUN dnf install -y epel-release
# dnf swap curl-minimal curl
RUN dnf install -y \
        rpm-build \
        git \
        pyproject-rpm-macros \
        python3-devel \
        python3-pip \
        python3-wheel \
        python3-build \
        python3-installer \
        python3-hatchling \
        python3-pytest \
        python3-tomli \
        python3-tomli-w \
        make \
        && \
    dnf clean all
