FROM python:latest

WORKDIR /
RUN mkdir app
WORKDIR /app
ADD main.py .
RUN pip install ogn-client
CMD ["python", "./main.py"]