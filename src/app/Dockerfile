FROM python:3.9-slim

# Disable output buffering so logs appear immediately in Docker
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /voidemon

WORKDIR /voidemon

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Gossip node HTTP API (Flask)
EXPOSE 5000

# Launch the VOIDemon gossip node entrypoint
CMD ["python", "./gossip_node.py"]