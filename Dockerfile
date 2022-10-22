FROM python:3.10
WORKDIR /app
COPY . .
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt
CMD ["python3.10","main.py"]