FROM python:3.10
WORKDIR /app
COPY ./requirements.txt /app
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3.10","main.py"]