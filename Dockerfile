FROM python:3.9
WORKDIR /streaming 
COPY requirements.txt .
RUN pip install -r requirements.txt 
COPY /streaming .
CMD ["python", "-m", "producer.main"]
