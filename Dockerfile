FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY strainer.py .

RUN mkdir -p data

CMD ["python", "strainer.py"]

# `sudo docker build -t proxy-strainer .`
# `sudo docker run -it --rm -v "$(pwd)/data:/app/data" proxy-strainer`