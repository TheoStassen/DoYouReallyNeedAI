# Dockerfile
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# install common tools, Node.js (for copilot CLI), and required certs
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     curl ca-certificates gnupg lsb-release build-essential \
  && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
  && apt-get install -y nodejs \
  && rm -rf /var/lib/apt/lists/*

# install GitHub CLI (gh)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
  && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list \
  && apt-get update \
  && apt-get install -y gh \
  && rm -rf /var/lib/apt/lists/*

# install Copilot CLI via npm (global)
RUN npm install  -g @github/copilot


WORKDIR /app

# copy requirements and install (ensure gunicorn is listed)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy application and entrypoint
COPY . /app
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/app/entrypoint.sh"]