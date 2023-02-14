FROM python:3.10
WORKDIR /app
COPY . .
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt
RUN git config --global --add safe.directory /app && git config pull.rebase false
CMD ["python3.10","main.py"]