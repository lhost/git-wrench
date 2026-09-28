FROM quay.io/centos/centos:stream9

RUN dnf config-manager --set-enabled crb
RUN dnf install -y epel-release
# dnf swap curl-minimal curl
RUN dnf install -y \
        rpm-build \
        python3-devel \
        python3-pip \
        python3-wheel \
        python3-build \
        python3-installer \
        python3-hatchling \
        make \
        && \
    dnf clean all
