SHELL:=/bin/bash

# First, set up WORKDIR to fit your system
ifeq ($(WORKDIR),)
  $(error The env variable WORKDIR is not set)
endif

# print WORKDIR info
$(info The env variable WORKDIR is set to: $(WORKDIR))

prerequisites:
	sudo apt-get update
	sudo apt-get install --fix-missing -y build-essential autoconf automake cmake nasm git htop tmux libtool zlib1g-dev gdb flex bison cmake nasm python-pip python3-pip texinfo clang && \
	sudo pip install wllvm && \
	sudo pip3 install networkx psutil pydot

# Fuzzers
aflsmart:
	git clone https://github.com/aflsmart/aflsmart.git

afl:
	git clone https://github.com/google/AFL.git afl
	cd afl && \
	git checkout 518e422 && \
	make clean all && \
	cd llvm_mode && \
	make

horsefuzz:
	git clone https://github.com/melbournefuzzinghub/horsefuzz.git horsefuzz
	cd horsefuzz && \
	make clean all && \
	mv afl-fuzz horse-fuzz && \
	cd llvm_mode && \
	make

# Subject programs
# LibPNG
libpng-afl:
	git clone https://github.com/glennrp/libpng.git libpng-afl
	cd libpng-afl && \
	git checkout 916117d && \
	sed -i 's/return ((int)(crc != png_ptr->crc));/return (0);/g' pngrutil.c && \
	autoreconf -f -i && \
	CC=afl-clang-fast ./configure --disable-shared && \
	make clean all

libpng-wllvm:
	git clone https://github.com/glennrp/libpng.git libpng-wllvm
	cd libpng-wllvm && \
	git checkout 916117d && \
	sed -i 's/return ((int)(crc != png_ptr->crc));/return (0);/g' pngrutil.c && \
	autoreconf -f -i && \
	CC=wllvm ./configure --disable-shared && \
	make clean all && \
	extract-bc -l llvm-link-6.0 pngimage && \
	opt-6.0 -analyze -dot-callgraph < pngimage.bc && \
	mv callgraph.dot pngimage.dot

libpng-horsefuzz:
	git clone https://github.com/glennrp/libpng.git libpng-horsefuzz
	cd libpng-horsefuzz && \
	git checkout 916117d && \
	sed -i 's/return ((int)(crc != png_ptr->crc));/return (0);/g' pngrutil.c && \
	autoreconf -f -i && \
	rm -rf /tmp/pngimage && mkdir /tmp/pngimage && \
	HF_BINARY=pngimage CC=horsefuzz-clang-fast ./configure --disable-shared && \
	HF_BINARY=pngimage make clean all && \
	mv /tmp/pngimage pngimage-horsefuzz-logs

libpng-horsefuzz-profiling:
	git clone https://github.com/glennrp/libpng.git libpng-horsefuzz-profiling
	cd libpng-horsefuzz-profiling && \
	git checkout 916117d && \
	sed -i 's/return ((int)(crc != png_ptr->crc));/return (0);/g' pngrutil.c && \
	autoreconf -f -i && \
	rm -rf /tmp/pngimage && mkdir /tmp/pngimage && \
	HF_BINARY=pngimage HORSEFUZZ_CG_PROFILING=1 CC=horsefuzz-clang-fast ./configure --disable-shared && \
	HF_BINARY=pngimage HORSEFUZZ_CG_PROFILING=1 make clean all && \
	mv /tmp/pngimage pngimage-horsefuzz-logs

libpng-cov:
	git clone https://github.com/glennrp/libpng.git libpng-cov
	cd libpng-cov && \
	git checkout 916117d97058b37e7eef2558a71919a8a073a3d3 && \
	sed -i 's/return ((int)(crc != png_ptr->crc));/return (0);/g' pngrutil.c && \
	autoreconf -f -i && \
	CFLAGS="-g -fprofile-arcs -ftest-coverage" ./configure --disable-shared && \
	make clean all

libpng-all: libpng-afl libpng-wllvm libpng-horsefuzz libpng-horsefuzz-profiling libpng-cov

libpng-clean-all:
	rm -rf libpng-afl libpng-wllvm libpng-horsefuzz libpng-horsefuzz-profiling libpng-cov

# LibJPEG-turbo
libjpeg-turbo-afl:
	git clone https://github.com/libjpeg-turbo/libjpeg-turbo.git libjpeg-turbo-afl
	cd libjpeg-turbo-afl && \
	git checkout dc9bdf143a1b5f19435a76e16a916817e1c255bf && \
	mkdir build && cd build && \
	CC=afl-clang-fast CXX=afl-clang-fast++ cmake -G"Unix Makefiles" .. && \
	make clean all

libjpeg-turbo-wllvm:
	git clone https://github.com/libjpeg-turbo/libjpeg-turbo.git libjpeg-turbo-wllvm
	cd libjpeg-turbo-wllvm && \
	git checkout dc9bdf143a1b5f19435a76e16a916817e1c255bf && \
	mkdir build && cd build && \
	CC=wllvm CXX=wllvm++ cmake -G"Unix Makefiles" .. && \
	make clean all && \
	extract-bc -l llvm-link-6.0 djpeg && \
	opt-6.0 -analyze -dot-callgraph < djpeg.bc && \
	mv callgraph.dot djpeg.dot

libjpeg-turbo-horsefuzz:
	git clone https://github.com/libjpeg-turbo/libjpeg-turbo.git libjpeg-turbo-horsefuzz
	cd libjpeg-turbo-horsefuzz && \
	git checkout dc9bdf143a1b5f19435a76e16a916817e1c255bf && \
	rm -rf /tmp/djpeg && mkdir /tmp/djpeg && \
	mkdir build && cd build && \
	HF_BINARY=djpeg CC=horsefuzz-clang-fast CXX=horsefuzz-clang-fast++ cmake -G"Unix Makefiles" .. && \
	HF_BINARY=djpeg make clean all && \
	mv /tmp/djpeg djpeg-horsefuzz-logs

libjpeg-turbo-horsefuzz-profiling:
	git clone https://github.com/libjpeg-turbo/libjpeg-turbo.git libjpeg-turbo-horsefuzz-profiling
	cd libjpeg-turbo-horsefuzz-profiling && \
	git checkout dc9bdf143a1b5f19435a76e16a916817e1c255bf && \
	rm -rf /tmp/djpeg && mkdir /tmp/djpeg && \
	mkdir build && cd build && \
	HF_BINARY=djpeg HORSEFUZZ_CG_PROFILING=1 CC=horsefuzz-clang-fast CXX=horsefuzz-clang-fast++ cmake -G"Unix Makefiles" .. && \
	HF_BINARY=djpeg HORSEFUZZ_CG_PROFILING=1 make clean all && \
	mv /tmp/djpeg djpeg-horsefuzz-logs

libjpeg-turbo-cov:
	git clone https://github.com/libjpeg-turbo/libjpeg-turbo.git libjpeg-turbo-cov
	cd libjpeg-turbo-cov && \
	git checkout dc9bdf143a1b5f19435a76e16a916817e1c255bf && \
	mkdir build && cd build && \
	cmake -G"Unix Makefiles" .. -DCMAKE_C_FLAGS="-g -fprofile-arcs -ftest-coverage" -DCMAKE_CXX_FLAGS="-g -fprofile-arcs -ftest-coverage" && \
	make clean all

libjpeg-turbo-all: libjpeg-turbo-afl libjpeg-turbo-wllvm libjpeg-turbo-horsefuzz libjpeg-turbo-horsefuzz-profiling libjpeg-turbo-cov

libjpeg-turbo-clean-all:
	rm -rf libjpeg-turbo-afl libjpeg-turbo-wllvm libjpeg-turbo-horsefuzz libjpeg-turbo-horsefuzz-profiling libjpeg-turbo-cov

#Jasper-commit: 543e18d-https://github.com/jasper-software/jasper/commit/543e18d0004dcf63b65b2ab4a22d3384517d7c22
jasper-afl:
	git clone https://github.com/mdadams/jasper.git jasper-afl
	cd jasper-afl && \
	git checkout 543e18d && \
	mkdir my-build && cd my-build && \
	CC=afl-clang-fast CXX=afl-clang-fast++ cmake -G"Unix Makefiles" .. && \
	make clean all

jasper-wllvm:
	git clone https://github.com/mdadams/jasper.git jasper-wllvm
	cd jasper-wllvm && \
	git checkout 543e18d && \
	mkdir my-build && cd my-build && \
	CC=wllvm CXX=wllvm++ cmake -G"Unix Makefiles" .. && \
	make clean all && \
	cd src/appl && \
	extract-bc -l llvm-link-6.0 jasper && \
	opt-6.0 -analyze -dot-callgraph < jasper.bc && \
	mv callgraph.dot jasper.dot

jasper-horsefuzz:
	git clone https://github.com/mdadams/jasper.git jasper-horsefuzz
	cd jasper-horsefuzz && \
	git checkout 543e18d && \
	rm -rf /tmp/jasper && mkdir /tmp/jasper && \
	mkdir my-build && cd my-build && \
	HF_BINARY=jasper CC=horsefuzz-clang-fast CXX=horsefuzz-clang-fast++ cmake -G"Unix Makefiles" .. && \
	HF_BINARY=jasper CC=horsefuzz-clang-fast CXX=horsefuzz-clang-fast++ make clean all && \
	mv /tmp/jasper jasper-horsefuzz-logs

jasper-horsefuzz-profiling:
	git clone https://github.com/mdadams/jasper.git jasper-horsefuzz-profiling
	cd jasper-horsefuzz-profiling && \
	git checkout 543e18d && \
	rm -rf /tmp/jasper && mkdir /tmp/jasper && \
	mkdir my-build && cd my-build && \
	HF_BINARY=jasper HORSEFUZZ_CG_PROFILING=1 CC=horsefuzz-clang-fast CXX=horsefuzz-clang-fast++ cmake -G"Unix Makefiles" .. && \
	HF_BINARY=jasper HORSEFUZZ_CG_PROFILING=1 CC=horsefuzz-clang-fast CXX=horsefuzz-clang-fast++ make clean all && \
	mv /tmp/jasper jasper-horsefuzz-logs

jasper-cov:
	git clone https://github.com/mdadams/jasper.git jasper-cov
	cd jasper-cov && \
	git checkout 543e18d && \
	mkdir my-build && cd my-build && \
	cmake -G"Unix Makefiles" .. -DCMAKE_C_FLAGS="-g -fprofile-arcs -ftest-coverage" -DCMAKE_CXX_FLAGS="-g -fprofile-arcs -ftest-coverage" && \
	make

jasper-all: jasper-afl jasper-wllvm jasper-horsefuzz jasper-horsefuzz-profiling jasper-cov

jasper-clean-all:
	rm -rf jasper-afl jasper-wllvm jasper-horsefuzz jasper-horsefuzz-profiling jasper-cov

#FFmpeg
ffmpeg-afl:
	git clone https://github.com/FFmpeg/FFmpeg.git ffmpeg-afl
	cd ffmpeg-afl && \
	git checkout e5ba5fab493bd2edb24da47940626b024ebd0371 && \
	./configure --cc=afl-clang-fast --cxx=afl-clang-fast++ --assert-level=2 && \
	make -j4

ffmpeg-wllvm:
	git clone https://github.com/FFmpeg/FFmpeg.git ffmpeg-wllvm
	cd ffmpeg-wllvm && \
	git checkout e5ba5fab493bd2edb24da47940626b024ebd0371 && \
	./configure --cc=wllvm --cxx=wllvm++ --assert-level=2 && \
	make -j4 && \
	extract-bc -l llvm-link-6.0 ffmpeg && \
	opt-6.0 -analyze -dot-callgraph < ffmpeg.bc && \
	mv callgraph.dot ffmpeg.dot

ffmpeg-horsefuzz:
	git clone https://github.com/FFmpeg/FFmpeg.git ffmpeg-horsefuzz
	cd ffmpeg-horsefuzz && \
	git checkout e5ba5fab493bd2edb24da47940626b024ebd0371 && \
	rm -rf /tmp/ffmpeg && mkdir /tmp/ffmpeg && \
	HF_BINARY=ffmpeg ./configure --cc=horsefuzz-clang-fast --cxx=horsefuzz-clang-fast++ --assert-level=2 && \
	HF_BINARY=ffmpeg make -j4 && \
	mv /tmp/ffmpeg ffmpeg-horsefuzz-logs

ffmpeg-horsefuzz-profiling:
	git clone https://github.com/FFmpeg/FFmpeg.git ffmpeg-horsefuzz-profiling
	cd ffmpeg-horsefuzz-profiling && \
	git checkout e5ba5fab493bd2edb24da47940626b024ebd0371 && \
	rm -rf /tmp/ffmpeg && mkdir /tmp/ffmpeg && \
	HF_BINARY=ffmpeg HORSEFUZZ_CG_PROFILING=1 ./configure --cc=horsefuzz-clang-fast --cxx=horsefuzz-clang-fast++ --assert-level=2 && \
	HF_BINARY=ffmpeg HORSEFUZZ_CG_PROFILING=1 make -j4 && \
	mv /tmp/ffmpeg ffmpeg-horsefuzz-logs

ffmpeg-cov:
	git clone https://github.com/FFmpeg/FFmpeg.git ffmpeg-cov
	cd ffmpeg-cov && \
	git checkout e5ba5fab493bd2edb24da47940626b024ebd0371 && \
	./configure --extra-cflags="-g -fprofile-arcs -ftest-coverage" --extra-ldflags="-g -fprofile-arcs -ftest-coverage" --assert-level=2 && \
	make -j4

ffmpeg-all: ffmpeg-afl ffmpeg-wllvm ffmpeg-horsefuzz ffmpeg-horsefuzz-profiling ffmpeg-cov

ffmpage-clean-all:
	rm -rf ffmpeg-afl ffmpeg-wllvm ffmpeg-horsefuzz ffmpeg-horsefuzz-profiling ffmpeg-cov

# All subjects
all-subjects: libpng-all libjpeg-turbo-all jasper-all ffmpeg-all

all-subjects-clean: libpng-clean-all libjpeg-turbo-clean-all jasper-clean-all ffmpeg-clean-all

all: prerequisites afl aflsmart all-subjects
