ARG DTK_IMAGE
ARG SIGNER_SDK_IMAGE
ARG DRIVER_IMAGE
ARG DRIVER_VERSION
ARG DRIVER_VENDOR
ARG AUTH_SECRET

FROM ${DTK_IMAGE} as dtk
USER root
ARG DRIVER_REPO DRIVER_VERSION ADDITIONAL_BUILD_DEPS

WORKDIR /home/builder
COPY --chmod=0755 scripts/build-commands.sh /home/builder/build-commands.sh
RUN if [ -n "$ADDITIONAL_BUILD_DEPS" ]; then \
       dnf -y install -- $ADDITIONAL_BUILD_DEPS && \
       dnf clean all && \
       rm -rf /var/cache/yum; \
    fi
RUN source /etc/driver-toolkit-release.sh && \
    echo $KERNEL_VERSION > /tmp/BUILD_KERNEL_VER && \
    git clone --depth 1 --branch $DRIVER_VERSION $DRIVER_REPO && \
    cd $(basename $DRIVER_REPO .git) && \
    /home/builder/build-commands.sh 

FROM ${DRIVER_IMAGE} 
ARG DRIVER_VERSION KERNEL_VERSION AUTH_SECRET DRIVER_VENDOR UPLOAD_ARTIFACT_REPO
COPY --from=dtk /home/builder/ /opt/drivers/
COPY --from=dtk /tmp/BUILD_KERNEL_VER /tmp/BUILD_KERNEL_VER
RUN echo "KERNEL_VERSION="$(cat /tmp/BUILD_KERNEL_VER) >> /opt/drivers/envfile && \
    echo "DRIVER_VERSION=${DRIVER_VERSION}" >> /opt/drivers/envfile && \
    echo "DRIVER_VENDOR=${DRIVER_VENDOR}" >> /opt/drivers/envfile

LABEL DRIVER_VERSION=$DRIVER_VERSION
LABEL KERNEL_VERSION=$KERNEL_VERSION
