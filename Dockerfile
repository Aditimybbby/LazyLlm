FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git curl wget build-essential nodejs npm \
    python3-dev libffi-dev libssl-dev procps \
    net-tools iputils-ping dnsutils ffmpeg \
    tesseract-ocr && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN npm install -g typescript ts-node

COPY . .

RUN mkdir -p uploads sessions static

EXPOSE 8000 11434

RUN ollama serve & sleep 10 && ollama pull codellama:13b-instruct && ollama pull mistral:7b-instruct

CMD ollama serve & sleep 15 && uvicorn main:app --host 0.0.0.0 --port $PORT
