FROM python:3.9-slim

RUN apt-get update && apt-get install -y build-essential

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
