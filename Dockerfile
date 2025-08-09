FROM python:3.10-slim
WORKDIR /app
COPY app/requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY app /app
CMD ["python", "main.py"]
