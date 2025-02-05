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
    /home/builder/build-commands.sh && \
    cp -p /usr/src/kernels/$KERNEL_VERSION/scripts/sign-file /usr/local/bin/sign-file

FROM ${SIGNER_SDK_IMAGE} as signer
ARG AUTH_SECRET AWS_DEFAULT_REGION AWS_KMS_KEY_LABEL GENKEY_FILE
USER root
COPY --from=dtk /home/builder /opt/drivers/
COPY --from=dtk /tmp/BUILD_KERNEL_VER /tmp/BUILD_KERNEL_VER
COPY --chmod=0755 --from=dtk /usr/local/bin/sign-file /usr/local/bin/sign-file
COPY --chmod=0755 set_pkcs11_engine /usr/bin/set_pkcs11_engine
COPY ssl/x509.keygen /etc/aws-kms-pkcs11/x509.genkey
RUN --mount=type=secret,id=${AUTH_SECRET}/AWS_KMS_TOKEN echo "export AWS_KMS_TOKEN="$(cat /run/secrets/${AUTH_SECRET}/AWS_KMS_TOKEN) >> /tmp/envfile 
RUN --mount=type=secret,id=${AUTH_SECRET}/AWS_ACCESS_KEY_ID echo "export AWS_ACCESS_KEY_ID="$(cat /run/secrets/${AUTH_SECRET}/AWS_ACCESS_KEY_ID) >> /tmp/envfile
RUN --mount=type=secret,id=${AUTH_SECRET}/AWS_SECRET_ACCESS_KEY echo "export AWS_SECRET_ACCESS_KEY="$(cat /run/secrets/${AUTH_SECRET}/AWS_SECRET_ACCESS_KEY) >> /tmp/envfile
RUN echo "export AWS_KMS_KEY_LABEL=${AWS_KMS_KEY_LABEL}" >> /tmp/envfile && \
    echo "export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}" >> /tmp/envfile && \
    source /tmp/envfile && \
    sed  -i '1i openssl_conf = openssl_init' /etc/pki/tls/openssl.cnf && \
    cat /etc/aws-kms-pkcs11/openssl-pkcs11.conf >> /etc/pki/tls/openssl.cnf && \
    cat <<EOF > /etc/aws-kms-pkcs11/config.json
{
  "slots": [
    {
      "label": "$AWS_KMS_KEY_LABEL",
      "kms_key_id": "$AWS_KMS_TOKEN",
      "aws_region": "$AWS_DEFAULT_REGION",
      "certificate_path": "/etc/aws-kms-pkcs11/cert.pem"
     }
           ]
}
EOF
RUN source /tmp/envfile && \
    export PKCS11_MODULE_PATH=/usr/lib64/pkcs11/aws_kms_pkcs11.so && \
    openssl req -config /etc/aws-kms-pkcs11/x509.genkey -x509 -key "pkcs11:model=0;manufacturer=aws_kms;serial=0;token=$AWS_KMS_KEY_LABEL" -keyform engine -engine pkcs11 -out /etc/aws-kms-pkcs11/cert.pem -days 36500 && \
    oot_modules="/opt/drivers/" && \
    find "$oot_modules" -type f -name "*.ko" | while IFS= read -r file; do \
        signedfile="${oot_modules}$(basename "${file%.*}")-signed.ko"; \
        echo "Signing ${file}\n"; \
        sign-file sha256 \
            "pkcs11:model=0;manufacturer=aws_kms;serial=0;token=$AWS_KMS_KEY_LABEL" \
            /etc/aws-kms-pkcs11/cert.pem \
            "$file" \
            "$signedfile"; \
    done	   
FROM ${DRIVER_IMAGE} 
ARG DRIVER_VERSION KERNEL_VERSION AUTH_SECRET DRIVER_VENDOR UPLOAD_ARTIFACT_REPO

COPY --from=signer /opt/drivers /opt/drivers
COPY --from=signer /tmp/BUILD_KERNEL_VER /tmp/BUILD_KERNEL_VER
RUN echo "export KERNEL_VERSION="$(cat /tmp/BUILD_KERNEL_VER) >> /tmp/envfile
RUN dnf -y install git git-lfs xz && \
    dnf clean all && \
    rm -rf /var/cache/yum
RUN --mount=type=secret,id=${AUTH_SECRET}/PRIVATE_GITLAB_TOKEN echo "export PRIVATE_GITLAB_TOKEN="$(cat /run/secrets/${AUTH_SECRET}/PRIVATE_GITLAB_TOKEN) >> /tmp/envfile
RUN source /tmp/envfile && \
    git clone https://gitlab-ci-token:${PRIVATE_GITLAB_TOKEN}@gitlab.com/ebelarte/artifact-storage.git && \
    cd artifact-storage && \
    git lfs install && \
    git lfs track "*.tar.xz" && \
    git remote set-url origin "https://gitlab-ci-token:${PRIVATE_GITLAB_TOKEN}@gitlab.com/ebelarte/artifact-storage.git" && \
    git config --global user.email "ebelarte-build-and-sign-tests@tests.redhat.com" && \
    git config --global user.name "CI build LFS bot" && \
    tar -cvJf ${DRIVER_VENDOR}-${DRIVER_VERSION}-${KERNEL_VERSION}.tar.xz /opt/drivers && \
    rm -rf /opt/drivers && \
    git add . && \
    git commit -m "Adding  ${DRIVER_VENDOR}-${DRIVER_VERSION}-${KERNEL_VERSION}.tar.xz" && \
    git push origin main

LABEL DRIVER_VERSION=$DRIVER_VERSION
LABEL KERNEL_VERSION=$KERNEL_VERSION
