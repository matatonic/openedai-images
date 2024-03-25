FROM python:3-slim

RUN mkdir -p /app/config
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py .
COPY config/default_*.json /app/config/

CMD python images.py