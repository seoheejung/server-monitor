FROM docker:26-cli

RUN apk add --no-cache python3 py3-pip shadow bash && \
    pip install --no-cache-dir ansible ansible-lint --break-system-packages

RUN ansible-galaxy collection install ansible.posix

WORKDIR /workspace