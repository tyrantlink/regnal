FROM python:3.11
WORKDIR /app
COPY . .
RUN git config --global --add safe.directory /app && git config pull.rebase false

RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

# hacky bullshit for maturin
ENV VIRTUAL_ENV="/usr/local"
RUN maturin develop -rm regnalrb/Cargo.toml

# fix tts spamming logs
ENV GRPC_ENABLE_FORK_SUPPORT=0

CMD mkdocs build -d doc_build && python3.11 -OO -u main.py