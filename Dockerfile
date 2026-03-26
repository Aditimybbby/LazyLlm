FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py *.html *.css *.js ./

RUN mkdir -p uploads

EXPOSE 8000

CMD ollama serve & sleep 10 && uvicorn main:app --host 0.0.0.0 --port $PORT
