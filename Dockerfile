FROM python:3-slim

RUN mkdir -p /app/config
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
COPY *.py .
COPY config/default_*.json /app/config/

CMD python images.py