.PHONY: all configure build test clean
BUILD_DIR ?= build
CMAKE ?= cmake
all: build
configure:
	$(CMAKE) -S . -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=Release
build: configure
	$(CMAKE) --build $(BUILD_DIR) --parallel
test: build
	ctest --test-dir $(BUILD_DIR) --output-on-failure
clean:
	rm -rf $(BUILD_DIR)
