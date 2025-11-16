FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install pymongo

EXPOSE 3000 5000

CMD ["python", "main.py"]