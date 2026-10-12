# This container serves the OctavianOS web desktop preview, not the OS kernel.
FROM nginx:1.27-alpine
LABEL org.opencontainers.image.title="OctavianOS Desktop Preview" \
      org.opencontainers.image.description="Web desktop companion; not a virtual machine or OS kernel"
COPY web/ /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=20s --timeout=3s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
