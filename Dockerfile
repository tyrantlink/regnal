FROM python:3.11
WORKDIR /app
COPY . .
RUN git config --global --add safe.directory /app && git config pull.rebase false
RUN sed -i -e's/ main/ main contrib non-free/g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update -qq && apt-get -y install \
	autoconf \
	automake \
	build-essential \
	cmake \
	git-core \
	libass-dev \
	libfreetype6-dev \
	libsdl2-dev \
	libtool \
	libva-dev \
	libvdpau-dev \
	libvorbis-dev \
	libxcb1-dev \
	libxcb-shm0-dev \
	libxcb-xfixes0-dev \
	pkg-config \
	texinfo \
	wget \
	zlib1g-dev \
	nasm \
	yasm \
	libx265-dev \
	libnuma-dev \
	libvpx-dev \
	libmp3lame-dev \
	libopus-dev \
	libx264-dev \
	libfdk-aac-dev
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN mkdir -p ~/ffmpeg_sources ~/bin && cd ~/ffmpeg_sources && \
	wget -O ffmpeg-4.2.2.tar.bz2 https://ffmpeg.org/releases/ffmpeg-4.2.2.tar.bz2 && \
	tar xjvf ffmpeg-4.2.2.tar.bz2 && \
	cd ffmpeg-4.2.2 && \
	PATH="$HOME/bin:$PATH" PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" ./configure \
		--prefix="$HOME/ffmpeg_build" \
		--pkg-config-flags="--static" \
		--extra-cflags="-I$HOME/ffmpeg_build/include" \
		--extra-ldflags="-L$HOME/ffmpeg_build/lib" \
		--extra-libs="-lpthread -lm" \
		--bindir="$HOME/bin" \
		--enable-libfdk-aac \
		--enable-gpl \
		--enable-libass \
		--enable-libfreetype \
		--enable-libmp3lame \
		--enable-libopus \
		--enable-libvorbis \
		--enable-libvpx \
		--enable-libx264 \
		--enable-libx265 \
		--enable-nonfree && \
	PATH="$HOME/bin:$PATH" make -j8 && \
	make install -j8 && \
	hash -r
RUN mv ~/bin/ffmpeg /usr/local/bin && mv ~/bin/ffprobe /usr/local/bin
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt
# hacky bullshit for maturin
ENV VIRTUAL_ENV="/usr/local"
RUN maturin develop -rm regnalrb/Cargo.toml
CMD mkdocs build -d doc_build && python3.11 -OO -u main.py