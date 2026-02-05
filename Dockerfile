# Dockerfile
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# install common tools and required certs
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     curl ca-certificates build-essential \
  && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# copy requirements and install (ensure gunicorn is listed)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Pre-download the SBERT model during build for faster startup
# This caches the model in the image so it doesn't download on each container start
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HOME=/app/.cache/huggingface
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# copy application and entrypoint
COPY . /app
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/app/entrypoint.sh"]