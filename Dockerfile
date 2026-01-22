FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONNUNBUFFERED=1 

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential ca-certificates \
 && rm -rf /var/lib/apt/lists/* 

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8050
CMD ["python", "app/app.py"]
