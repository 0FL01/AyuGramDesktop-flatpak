# syntax=docker/dockerfile:1

# Используем один основной образ для сборки
FROM rockylinux:8 AS builder
ENV LANG=C.UTF-8
ENV TOOLSET=gcc-toolset-14
ENV PATH=/opt/rh/$TOOLSET/root/usr/bin:$PATH
ENV LIBRARY_PATH=/opt/rh/$TOOLSET/root/usr/lib64:/opt/rh/$TOOLSET/root/usr/lib:/usr/local/lib64:/usr/local/lib:/lib64:/lib:/usr/lib64:/usr/lib
ENV LD_LIBRARY_PATH=$LIBRARY_PATH
ENV PKG_CONFIG_PATH=/opt/rh/$TOOLSET/root/usr/lib64/pkgconfig:/opt/rh/$TOOLSET/root/usr/lib/pkgconfig:/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:/usr/local/share/pkgconfig

# Устанавливаем все необходимые системные зависимости в одном слое
RUN dnf -y install epel-release \
	&& dnf config-manager --set-enabled powertools \
	&& dnf -y install cmake autoconf automake libtool pkgconfig make patch git \
		python3.11-pip python3.11-devel gperf flex bison clang clang-tools-extra \
		lld nasm yasm file which wget perl-open perl-XML-Parser perl-IPC-Cmd \
		xorg-x11-util-macros $TOOLSET-gcc $TOOLSET-gcc-c++ $TOOLSET-binutils \
		$TOOLSET-gdb $TOOLSET-libasan-devel libffi-devel fontconfig-devel \
		freetype-devel libX11-devel wayland-devel alsa-lib-devel \
		pulseaudio-libs-devel mesa-libGL-devel mesa-libEGL-devel mesa-libgbm-devel \
		libdrm-devel vulkan-devel libva-devel libvdpau-devel libselinux-devel \
		libmount-devel systemd-devel glib2-devel gobject-introspection-devel \
		at-spi2-core-devel gtk3-devel boost1.78-devel \
	&& dnf clean all

# Настраиваем окружение: python, pkg-config, cmake, gdb
RUN alternatives --set python3 /usr/bin/python3.11 \
	&& python3 -m pip install meson ninja \
	&& cat <<EOF > /usr/local/bin/pkg-config && chmod +x /usr/local/bin/pkg-config \
#!/bin/sh
for i in "\$@"; do
	[ "\$i" = "--version" ] && exec /usr/bin/pkg-config "\$i"
done
exec /usr/bin/pkg-config --static "\$@"
EOF \
	&& sed -i '/CMAKE_${lang}_FLAGS_DEBUG_INIT/s/")/ -Os {% if LTO %}-fno-lto -fno-use-linker-plugin -fuse-ld=lld{% endif %}")/' /usr/share/cmake/Modules/Compiler/GNU.cmake \
	&& sed -i 's/NO_DEFAULT_PATH//g; s/PKG_CONFIG_ALLOW_SYSTEM_LIBS/PKG_CONFIG_IS_DUMB/g' /usr/share/cmake/Modules/FindPkgConfig.cmake \
	&& sed -i 's/set(OpenGL_GL_PREFERENCE "")/set(OpenGL_GL_PREFERENCE "LEGACY")/' /usr/share/cmake/Modules/FindOpenGL.cmake \
	&& sed -i '/Requires.private: valgrind/d' /usr/lib64/pkgconfig/libdrm.pc \
	&& sed -i 's/-lharfbuzz//' /usr/lib64/pkgconfig/harfbuzz.pc \
	&& sed -i 's/-lpng16//' /usr/lib64/pkgconfig/libpng16.pc \
	&& echo set debuginfod enabled on > /opt/rh/$TOOLSET/root/etc/gdbinit.d/00-debuginfod.gdb \
	&& adduser user

# Устанавливаем переменные окружения для компиляции
WORKDIR /usr/src
ENV AR=gcc-ar
ENV RANLIB=gcc-ranlib
ENV NM=gcc-nm
ENV CFLAGS='{% if DEBUG %}-g{% endif %} -Os {% if LTO %}-flto=auto -ffat-lto-objects{% endif %} -pipe -fPIC -fno-strict-aliasing -fexceptions -fasynchronous-unwind-tables -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer -fhardened -Wno-hardened'
ENV CXXFLAGS=$CFLAGS
ENV LDFLAGS='{% if not LTO %}-fuse-ld=lld{% endif %} -static-libstdc++ -static-libgcc -static-libasan -pthread -ldl -Wl,--as-needed -Wl,-z,muldefs'

ENV CMAKE_GENERATOR=Ninja
ENV CMAKE_BUILD_TYPE=None
ENV CMAKE_BUILD_PARALLEL_LEVEL='{{ JOBS }}'

# --- ЕДИНЫЙ СЛОЙ СБОРКИ ВСЕХ ЗАВИСИМОСТЕЙ ---
# Все зависимости собираются и устанавливаются последовательно в одной инструкции RUN.
# Исходные коды удаляются сразу после установки, чтобы не увеличивать размер итогового слоя.
RUN \
	# --- Сборка Implib.so ---
	git init Implib.so \
	&& cd Implib.so \
	&& git remote add origin https://github.com/yugr/Implib.so.git \
	&& git fetch --depth=1 origin ecf7bb51a92a0fb16834c5b698570ab25f9f1d21 \
	&& git reset --hard FETCH_HEAD \
	&& mkdir build \
	&& cd build \
	&& implib() { \
		LIBFILE=$(basename $1); \
		LIBNAME=$(basename $1 .so); \
		../implib-gen.py -q $1; \
		gcc $CFLAGS -c -o $LIBFILE.tramp.o $LIBFILE.tramp.S; \
		gcc $CFLAGS -c -o $LIBFILE.init.o $LIBFILE.init.c; \
		ar rcs /usr/local/lib64/$LIBNAME.a $LIBFILE.tramp.o $LIBFILE.init.o; \
	} \
	&& implib /usr/lib64/libgtk-3.so \
	&& implib /usr/lib64/libgdk-3.so \
	&& implib /usr/lib64/libgdk_pixbuf-2.0.so \
	&& implib /usr/lib64/libpango-1.0.so \
	&& implib /usr/lib64/libvdpau.so \
	&& implib /usr/lib64/libva-x11.so \
	&& implib /usr/lib64/libva-drm.so \
	&& implib /usr/lib64/libva.so \
	&& implib /usr/lib64/libEGL.so \
	&& implib /usr/lib64/libGL.so \
	&& implib /usr/lib64/libdrm.so \
	&& implib /usr/lib64/libwayland-egl.so \
	&& implib /usr/lib64/libwayland-cursor.so \
	&& implib /usr/lib64/libwayland-client.so \
	&& implib /usr/lib64/libwayland-server.so \
	&& implib /usr/lib64/libX11-xcb.so \
	&& implib /usr/lib64/libxcb.so \
	&& cd ../.. \
	&& rm -rf Implib.so \
	\
	# --- Клонирование патчей ---
	&& git init patches \
	&& cd patches \
	&& git remote add origin https://github.com/desktop-app/patches.git \
	&& git fetch --depth=1 origin 1ffcb17817a2cab167061d530703842395291e69 \
	&& git reset --hard FETCH_HEAD \
	&& rm -rf .git \
	&& cd .. \
	\
	# --- Сборка zlib ---
	&& git clone -b v1.3.1 --depth=1 https://github.com/madler/zlib.git \
	&& cd zlib \
	&& cmake -B build . -DZLIB_BUILD_EXAMPLES=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& rm /usr/local/lib/libz.so* \
	&& cd .. \
	&& rm -rf zlib \
	\
	# --- Сборка xz ---
	&& git clone -b v5.8.1 --depth=1 https://github.com/tukaani-project/xz.git \
	&& cd xz \
	&& cmake -B build . \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf xz \
	\
	# --- Сборка protobuf ---
	&& git clone -b v30.2 --depth=1 --recursive --shallow-submodules https://github.com/protocolbuffers/protobuf.git \
	&& cd protobuf \
	&& cmake -B build . \
		-Dprotobuf_BUILD_TESTS=OFF \
		-Dprotobuf_BUILD_PROTOBUF_BINARIES=ON \
		-Dprotobuf_BUILD_LIBPROTOC=ON \
		-Dprotobuf_WITH_ZLIB=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf protobuf \
	\
	# --- Сборка lcms2 ---
	&& git clone -b lcms2.15 --depth=1 https://github.com/mm2/Little-CMS.git \
	&& cd Little-CMS \
	&& meson build --buildtype=plain --default-library=static \
	&& meson compile -C build \
	&& meson install -C build \
	&& cd .. \
	&& rm -rf Little-CMS \
	\
	# --- Сборка brotli ---
	&& git clone -b v1.1.0 --depth=1 https://github.com/google/brotli.git \
	&& cd brotli \
	&& cmake -B build . -DBUILD_SHARED_LIBS=OFF -DBROTLI_DISABLE_TESTS=ON \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf brotli \
	\
	# --- Сборка highway ---
	&& git clone -b 1.0.7 --depth=1 https://github.com/google/highway.git \
	&& cd highway \
	&& cmake -B build . -DBUILD_TESTING=OFF -DHWY_ENABLE_CONTRIB=OFF -DHWY_ENABLE_EXAMPLES=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf highway \
	\
	# --- Сборка opus ---
	&& git clone -b v1.5.2 --depth=1 https://github.com/xiph/opus.git \
	&& cd opus \
	&& cmake -B build . \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf opus \
	\
	# --- Сборка dav1d ---
	&& git clone -b 1.5.1 --depth=1 https://github.com/videolan/dav1d.git \
	&& cd dav1d \
	&& meson build --buildtype=plain --default-library=static -Denable_tools=false -Denable_tests=false \
	&& meson compile -C build \
	&& meson install -C build \
	&& cd .. \
	&& rm -rf dav1d \
	\
	# --- Сборка openh264 ---
	&& git clone -b v2.6.0 --depth=1 https://github.com/cisco/openh264.git \
	&& cd openh264 \
	&& meson build --buildtype=plain --default-library=static \
	&& meson compile -C build \
	&& meson install -C build \
	&& cd .. \
	&& rm -rf openh264 \
	\
	# --- Сборка de265 ---
	&& git clone -b v1.0.16 --depth=1 https://github.com/strukturag/libde265.git \
	&& cd libde265 \
	&& cmake -B build . -DCMAKE_BUILD_TYPE=None -DBUILD_SHARED_LIBS=OFF -DENABLE_DECODER=OFF -DENABLE_SDL=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf libde265 \
	\
	# --- Сборка vpx ---
	&& git init libvpx \
	&& cd libvpx \
	&& git remote add origin https://github.com/webmproject/libvpx.git \
	&& git fetch --depth=1 origin 12f3a2ac603e8f10742105519e0cd03c3b8f71dd \
	&& git reset --hard FETCH_HEAD \
	&& CFLAGS="$CFLAGS -fno-lto" CXXFLAGS="$CXXFLAGS -fno-lto" ./configure --disable-examples --disable-unit-tests --disable-tools --disable-docs --enable-vp8 --enable-vp9 --enable-webm-io --size-limit=4096x4096 \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libvpx \
	\
	# --- Сборка webp ---
	&& git clone -b v1.5.0 --depth=1 https://github.com/webmproject/libwebp.git \
	&& cd libwebp \
	&& cmake -B build . -DWEBP_BUILD_ANIM_UTILS=OFF -DWEBP_BUILD_CWEBP=OFF -DWEBP_BUILD_DWEBP=OFF -DWEBP_BUILD_GIF2WEBP=OFF -DWEBP_BUILD_IMG2WEBP=OFF -DWEBP_BUILD_VWEBP=OFF -DWEBP_BUILD_WEBPMUX=OFF -DWEBP_BUILD_WEBPINFO=OFF -DWEBP_BUILD_EXTRAS=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf libwebp \
	\
	# --- Сборка avif (зависит от dav1d) ---
	&& git clone -b v1.3.0 --depth=1 https://github.com/AOMediaCodec/libavif.git \
	&& cd libavif \
	&& cmake -B build . -DBUILD_SHARED_LIBS=OFF -DAVIF_CODEC_DAV1D=SYSTEM -DAVIF_LIBYUV=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf libavif \
	\
	# --- Сборка heif (зависит от de265) ---
	&& git clone -b v1.19.8 --depth=1 https://github.com/strukturag/libheif.git \
	&& cd libheif \
	&& cmake -B build . -DBUILD_SHARED_LIBS=OFF -DBUILD_TESTING=OFF -DENABLE_PLUGIN_LOADING=OFF -DWITH_X265=OFF -DWITH_AOM_DECODER=OFF -DWITH_AOM_ENCODER=OFF -DWITH_OpenH264_DECODER=OFF -DWITH_RAV1E=OFF -DWITH_RAV1E_PLUGIN=OFF -DWITH_SvtEnc=OFF -DWITH_SvtEnc_PLUGIN=OFF -DWITH_DAV1D=OFF -DWITH_LIBSHARPYUV=OFF -DWITH_EXAMPLES=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf libheif \
	\
	# --- Сборка jxl (зависит от lcms2, brotli, highway) ---
	&& git clone -b v0.11.1 --depth=1 https://github.com/libjxl/libjxl.git \
	&& cd libjxl \
	&& git submodule update --init --recursive --depth=1 third_party/libjpeg-turbo \
	&& cmake -B build . -DBUILD_SHARED_LIBS=OFF -DBUILD_TESTING=OFF -DJPEGXL_ENABLE_DEVTOOLS=OFF -DJPEGXL_ENABLE_TOOLS=OFF -DJPEGXL_INSTALL_JPEGLI_LIBJPEG=ON -DJPEGXL_ENABLE_DOXYGEN=OFF -DJPEGXL_ENABLE_MANPAGES=OFF -DJPEGXL_ENABLE_BENCHMARK=OFF -DJPEGXL_ENABLE_EXAMPLES=OFF -DJPEGXL_ENABLE_JNI=OFF -DJPEGXL_ENABLE_SJPEG=OFF -DJPEGXL_ENABLE_OPENEXR=OFF -DJPEGXL_ENABLE_SKCMS=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& sed -i 's/-lstdc++//' /usr/local/lib64/pkgconfig/libjxl*.pc \
	&& rm /usr/local/lib64/libjpeg.so* \
	&& cp build/lib/libjpegli-static.a /usr/local/lib64/libjpeg.a \
	&& mkdir build/hwy \
	&& ar --output=build/hwy x /usr/local/lib64/libhwy.a \
	&& ar rcs /usr/local/lib64/libjpeg.a build/lib/CMakeFiles/jpegli-libjpeg-obj.dir/jpegli/libjpeg_wrapper.cc.o build/hwy/* \
	&& cd .. \
	&& rm -rf libjxl \
	\
	# --- Сборка rnnoise ---
	&& git clone -b v0.2 --depth=1 https://github.com/xiph/rnnoise.git \
	&& cd rnnoise \
	&& ./autogen.sh \
	&& ./configure --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf rnnoise \
	\
	# --- Сборка xcb-proto ---
	&& git clone -b xcb-proto-1.16.0 --depth=1 https://github.com/gitlab-freedesktop-mirrors/xcbproto.git \
	&& cd xcbproto \
	&& ./autogen.sh \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf xcbproto \
	\
	# --- Сборка xcb (зависит от xcb-proto) ---
	&& git clone -b libxcb-1.16 --depth=1 https://github.com/gitlab-freedesktop-mirrors/libxcb.git \
	&& cd libxcb \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& rm /usr/local/lib/{libxcb.{,l}a,pkgconfig/xcb.pc} \
	&& cd .. \
	&& rm -rf libxcb \
	\
	# --- Сборка xcb-wm ---
	&& git clone -b xcb-util-wm-0.4.2 --depth=1 --recursive --shallow-submodules https://github.com/gitlab-freedesktop-mirrors/libxcb-wm.git \
	&& cd libxcb-wm \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxcb-wm \
	\
	# --- Сборка xcb-util ---
	&& git clone -b xcb-util-0.4.1-gitlab --depth=1 --recursive --shallow-submodules https://github.com/gitlab-freedesktop-mirrors/libxcb-util.git \
	&& cd libxcb-util \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxcb-util \
	\
	# --- Сборка xcb-image (зависит от xcb-util) ---
	&& git clone -b xcb-util-image-0.4.1-gitlab --depth=1 --recursive --shallow-submodules https://github.com/gitlab-freedesktop-mirrors/libxcb-image.git \
	&& cd libxcb-image \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxcb-image \
	\
	# --- Сборка xcb-keysyms ---
	&& git init libxcb-keysyms \
	&& cd libxcb-keysyms \
	&& git remote add origin https://github.com/gitlab-freedesktop-mirrors/libxcb-keysyms.git \
	&& git fetch --depth=1 origin ef5cb393d27511ba511c68a54f8ff7b9aab4a384 \
	&& git reset --hard FETCH_HEAD \
	&& git submodule update --init --recursive --depth=1 \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxcb-keysyms \
	\
	# --- Сборка xcb-render-util ---
	&& git init libxcb-render-util \
	&& cd libxcb-render-util \
	&& git remote add origin https://github.com/gitlab-freedesktop-mirrors/libxcb-render-util.git \
	&& git fetch --depth=1 origin 5ad9853d6ddcac394d42dd2d4e34436b5db9da39 \
	&& git reset --hard FETCH_HEAD \
	&& git submodule update --init --recursive --depth=1 \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxcb-render-util \
	\
	# --- Сборка xcb-cursor (зависит от xcb-util, xcb-image, xcb-render-util) ---
	&& git init libxcb-cursor \
	&& cd libxcb-cursor \
	&& git remote add origin https://github.com/gitlab-freedesktop-mirrors/libxcb-cursor.git \
	&& git fetch --depth=1 origin 4929f6051658ba5424b41703a1fb63f9db896065 \
	&& git reset --hard FETCH_HEAD \
	&& git submodule update --init --recursive --depth=1 \
	&& ./autogen.sh --enable-static --disable-shared --with-cursorpath='~/.local/share/icons:~/.icons:/usr/share/icons:/usr/share/pixmaps' \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxcb-cursor \
	\
	# --- Сборка xext ---
	&& git clone -b libXext-1.3.5 --depth=1 https://github.com/gitlab-freedesktop-mirrors/libxext.git \
	&& cd libxext \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxext \
	\
	# --- Сборка xtst ---
	&& git clone -b libXtst-1.2.4 --depth=1 https://github.com/gitlab-freedesktop-mirrors/libxtst.git \
	&& cd libxtst \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxtst \
	\
	# --- Сборка xfixes ---
	&& git clone -b libXfixes-5.0.3 --depth=1 https://github.com/gitlab-freedesktop-mirrors/libxfixes.git \
	&& cd libxfixes \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxfixes \
	\
	# --- Сборка xv (зависит от xext) ---
	&& git clone -b libXv-1.0.12 --depth=1 https://github.com/gitlab-freedesktop-mirrors/libxv.git \
	&& cd libxv \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxv \
	\
	# --- Сборка xrandr ---
	&& git clone -b libXrandr-1.5.3 --depth=1 https://github.com/gitlab-freedesktop-mirrors/libxrandr.git \
	&& cd libxrandr \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxrandr \
	\
	# --- Сборка xrender ---
	&& git clone -b libXrender-0.9.11 --depth=1 https://github.com/gitlab-freedesktop-mirrors/libxrender.git \
	&& cd libxrender \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxrender \
	\
	# --- Сборка xdamage ---
	&& git clone -b libXdamage-1.1.6 --depth=1 https://github.com/gitlab-freedesktop-mirrors/libxdamage.git \
	&& cd libxdamage \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxdamage \
	\
	# --- Сборка xcomposite ---
	&& git clone -b libXcomposite-0.4.6 --depth=1 https://github.com/gitlab-freedesktop-mirrors/libxcomposite.git \
	&& cd libxcomposite \
	&& ./autogen.sh --enable-static --disable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf libxcomposite \
	\
	# --- Сборка wayland ---
	&& git clone -b 1.19.0 --depth=1 https://github.com/gitlab-freedesktop-mirrors/wayland.git \
	&& cd wayland \
	&& sed -i "/subdir('tests')/d" meson.build \
	&& meson build --buildtype=plain --default-library=static -Ddocumentation=false -Ddtd_validation=false -Dicon_directory=/usr/share/icons \
	&& meson compile -C build src/wayland-scanner \
	&& mkdir -p "/usr/local/bin" "/usr/local/lib64/pkgconfig" \
	&& cp build/src/wayland-scanner "/usr/local/bin" \
	&& sed 's@bindir=${prefix}/bin@bindir=${prefix}/local/bin@;s/1.21.0/1.19.0/' /usr/lib64/pkgconfig/wayland-scanner.pc > "/usr/local/lib64/pkgconfig/wayland-scanner.pc" \
	&& cd .. \
	&& rm -rf wayland \
	\
	# --- Сборка nv-codec-headers ---
	&& git clone -b n12.1.14.0 --depth=1 https://github.com/FFmpeg/nv-codec-headers.git \
	&& make -C nv-codec-headers install \
	&& rm -rf nv-codec-headers \
	\
	# --- Сборка ffmpeg ---
	&& git clone -b n6.1.1 --depth=1 https://github.com/FFmpeg/FFmpeg.git \
	&& cd FFmpeg \
	&& ./configure --extra-cflags="-fno-lto -DCONFIG_SAFE_BITSTREAM_READER=1" --extra-cxxflags="-fno-lto -DCONFIG_SAFE_BITSTREAM_READER=1" --extra-ldflags="-lstdc++" --disable-debug --disable-programs --disable-doc --disable-network --disable-autodetect --disable-everything --enable-libdav1d --enable-libopenh264 --enable-libopus --enable-libvpx --enable-vaapi --enable-vdpau --enable-xlib --enable-libdrm --enable-ffnvcodec --enable-nvdec --enable-cuvid --enable-protocol=file --enable-hwaccel=av1_vaapi --enable-hwaccel=av1_nvdec --enable-hwaccel=h264_vaapi --enable-hwaccel=h264_vdpau --enable-hwaccel=h264_nvdec --enable-hwaccel=hevc_vaapi --enable-hwaccel=hevc_vdpau --enable-hwaccel=hevc_nvdec --enable-hwaccel=mpeg2_vaapi --enable-hwaccel=mpeg2_vdpau --enable-hwaccel=mpeg2_nvdec --enable-hwaccel=mpeg4_vaapi --enable-hwaccel=mpeg4_vdpau --enable-hwaccel=mpeg4_nvdec --enable-hwaccel=vp8_vaapi --enable-hwaccel=vp8_nvdec --enable-decoder=aac --enable-decoder=aac_fixed --enable-decoder=aac_latm --enable-decoder=aasc --enable-decoder=ac3 --enable-decoder=alac --enable-decoder=av1 --enable-decoder=av1_cuvid --enable-decoder=eac3 --enable-decoder=flac --enable-decoder=gif --enable-decoder=h264 --enable-decoder=hevc --enable-decoder=libdav1d --enable-decoder=libvpx_vp8 --enable-decoder=libvpx_vp9 --enable-decoder=mp1 --enable-decoder=mp1float --enable-decoder=mp2 --enable-decoder=mp2float --enable-decoder=mp3 --enable-decoder=mp3adu --enable-decoder=mp3adufloat --enable-decoder=mp3float --enable-decoder=mp3on4 --enable-decoder=mp3on4float --enable-decoder=mpeg4 --enable-decoder=msmpeg4v2 --enable-decoder=msmpeg4v3 --enable-decoder=opus --enable-decoder=pcm_alaw --enable-decoder=pcm_f32be --enable-decoder=pcm_f32le --enable-decoder=pcm_f64be --enable-decoder=pcm_f64le --enable-decoder=pcm_lxf --enable-decoder=pcm_mulaw --enable-decoder=pcm_s16be --enable-decoder=pcm_s16be_planar --enable-decoder=pcm_s16le --enable-decoder=pcm_s16le_planar --enable-decoder=pcm_s24be --enable-decoder=pcm_s24daud --enable-decoder=pcm_s24le --enable-decoder=pcm_s24le_planar --enable-decoder=pcm_s32be --enable-decoder=pcm_s32le --enable-decoder=pcm_s32le_planar --enable-decoder=pcm_s64be --enable-decoder=pcm_s64le --enable-decoder=pcm_s8 --enable-decoder=pcm_s8_planar --enable-decoder=pcm_u16be --enable-decoder=pcm_u16le --enable-decoder=pcm_u24be --enable-decoder=pcm_u24le --enable-decoder=pcm_u32be --enable-decoder=pcm_u32le --enable-decoder=pcm_u8 --enable-decoder=pcm_zork --enable-decoder=vorbis --enable-decoder=vp8 --enable-decoder=wavpack --enable-decoder=wmalossless --enable-decoder=wmapro --enable-decoder=wmav1 --enable-decoder=wmav2 --enable-decoder=wmavoice --enable-encoder=aac --enable-encoder=libopenh264 --enable-encoder=libopus --enable-encoder=pcm_s16le --enable-filter=atempo --enable-parser=aac --enable-parser=aac_latm --enable-parser=flac --enable-parser=gif --enable-parser=h264 --enable-parser=hevc --enable-parser=mpeg4video --enable-parser=mpegaudio --enable-parser=opus --enable-parser=vorbis --enable-demuxer=aac --enable-demuxer=flac --enable-demuxer=gif --enable-demuxer=h264 --enable-demuxer=hevc --enable-demuxer=matroska --enable-demuxer=m4v --enable-demuxer=mov --enable-demuxer=mp3 --enable-demuxer=ogg --enable-demuxer=wav --enable-muxer=mp4 --enable-muxer=ogg --enable-muxer=opus --enable-muxer=wav \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf FFmpeg \
	\
	# --- Сборка pipewire ---
	&& git clone -b 0.3.62 --depth=1 https://github.com/PipeWire/pipewire.git \
	&& cd pipewire \
	&& meson build --buildtype=plain -Dtests=disabled -Dexamples=disabled -Dsession-managers=media-session -Dspa-plugins=disabled \
	&& meson compile -C build \
	&& meson install -C build \
	&& cd .. \
	&& rm -rf pipewire \
	\
	# --- Сборка openal (зависит от pipewire) ---
	&& git clone -b 1.24.3 --depth=1 https://github.com/kcat/openal-soft.git \
	&& cd openal-soft \
	&& cmake -B build . -DLIBTYPE:STRING=STATIC -DALSOFT_EXAMPLES=OFF -DALSOFT_UTILS=OFF -DALSOFT_INSTALL_CONFIG=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf openal-soft \
	\
	# --- Сборка openssl ---
	&& git clone -b openssl-3.2.1 --depth=1 https://github.com/openssl/openssl.git \
	&& cd openssl \
	&& ./config --openssldir=/etc/ssl no-shared no-tests no-dso \
	&& make -j$(nproc) \
	&& make install_sw \
	&& cd .. \
	&& rm -rf openssl \
	\
	# --- Сборка xkbcommon (зависит от xcb) ---
	&& git clone -b xkbcommon-1.6.0 --depth=1 https://github.com/xkbcommon/libxkbcommon.git \
	&& cd libxkbcommon \
	&& meson build --buildtype=plain --default-library=static -Denable-docs=false -Denable-wayland=false -Denable-xkbregistry=false -Dxkb-config-root=/usr/share/X11/xkb -Dxkb-config-extra-path=/etc/xkb -Dx-locale-root=/usr/share/X11/locale \
	&& meson compile -C build \
	&& meson install -C build \
	&& cd .. \
	&& rm -rf libxkbcommon \
	\
	# --- Сборка qt ---
	&& export QT=6.9.1 \
	&& git clone -b v$QT --depth=1 https://github.com/qt/qt5.git \
	&& cd qt5 \
	&& git submodule update --init --recursive --depth=1 qtbase qtdeclarative qtwayland qtimageformats qtsvg qtshadertools \
	&& cd qtbase \
	&& find ../../patches/qtbase_$QT -type f -print0 | sort -z | xargs -r0 git apply \
	&& cd ../qtwayland \
	&& find ../../patches/qtwayland_$QT -type f -print0 | sort -z | xargs -r0 git apply \
	&& cd .. \
	&& cmake -B build . -DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_SHARED_LIBS=OFF -DQT_QPA_PLATFORMS="wayland;xcb" -DINPUT_libpng=qt -DINPUT_harfbuzz=qt -DINPUT_pcre=qt -DFEATURE_icu=OFF -DFEATURE_xcb_sm=OFF -DFEATURE_eglfs=OFF -DINPUT_dbus=runtime -DINPUT_openssl=linked \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf qt5 \
	\
	# --- Сборка breakpad ---
	&& git clone -b v2024.02.16 --depth=1 https://chromium.googlesource.com/breakpad/breakpad.git \
	&& cd breakpad \
	&& git clone -b v2024.02.01 --depth=1 https://chromium.googlesource.com/linux-syscall-support.git src/third_party/lss \
	&& CFLAGS="$CFLAGS -fno-lto" CXXFLAGS="$CXXFLAGS -fno-lto" ./configure \
	&& make -j$(nproc) \
	&& make install \
	&& cd .. \
	&& rm -rf breakpad \
	\
	# --- Сборка webrtc ---
	&& git init tg_owt \
	&& cd tg_owt \
	&& git remote add origin https://github.com/desktop-app/tg_owt.git \
	&& git fetch --depth=1 origin 62321fd7128ab2650b459d4195781af8185e46b5 \
	&& git reset --hard FETCH_HEAD \
	&& git submodule update --init --recursive --depth=1 \
	&& cmake -B build . -DTG_OWT_DLOPEN_PIPEWIRE=ON \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf tg_owt \
	\
	# --- Сборка ada ---
	&& git clone -b v3.2.4 --depth=1 https://github.com/ada-url/ada.git \
	&& cd ada \
	&& cmake -B build . -D ADA_TESTING=OFF -D ADA_TOOLS=OFF -D ADA_INCLUDE_URL_PATTERN=OFF \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf ada \
	\
	# --- Сборка tde2e ---
	&& git init tde2e \
	&& cd tde2e \
	&& git remote add origin https://github.com/tdlib/td.git \
	&& git fetch --depth=1 origin 51743dfd01dff6179e2d8f7095729caa4e2222e9 \
	&& git reset --hard FETCH_HEAD \
	&& cmake -B build . -DTD_E2E_ONLY=ON \
	&& cmake --build build \
	&& cmake --install build \
	&& cd .. \
	&& rm -rf tde2e \
	\
	# --- Применение финальных патчей ---
	&& patch -p1 -d /usr/lib64/gobject-introspection -i $PWD/patches/gobject-introspection.patch \
	&& rm -rf patches

# Финальная настройка для запуска основного скрипта сборки
WORKDIR /usr/src/tdesktop
ENV BOOST_INCLUDEDIR=/usr/include/boost1.78
ENV BOOST_LIBRARYDIR=/usr/lib64/boost1.78

USER user
VOLUME [ "/usr/src/tdesktop" ]
CMD [ "/usr/src/tdesktop/Telegram/build/docker/centos_env/build.sh" ]