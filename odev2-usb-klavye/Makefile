# USB Makro Klavye — çekirdek, benzetim ve testler için derleme.
# Donanım (STM32) tarafı Arduino IDE/arduino-cli ile derlenir; bkz. arduino/BENIOKU.md.

CXX      ?= g++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -O2
BIN      := bin

CEKIRDEK := $(wildcard cekirdek/*.cpp)
TEST_SRC := $(wildcard testler/*.cpp)

.PHONY: all test benzetim temizle
all: $(BIN)/testler $(BIN)/benzetim

$(BIN):
	mkdir -p $(BIN)

$(BIN)/testler: $(CEKIRDEK) $(TEST_SRC) | $(BIN)
	$(CXX) $(CXXFLAGS) $(CEKIRDEK) $(TEST_SRC) -o $@

$(BIN)/benzetim: $(CEKIRDEK) benzetim/main.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(CEKIRDEK) benzetim/main.cpp -o $@

# Testleri çalıştır (başarısızsa sıfırdan farklı kod döner).
test: $(BIN)/testler
	./$(BIN)/testler

# Benzetimi çalıştır. Kendi ayarınla:  make benzetim AYAR=ornek_ayar.conf
benzetim: $(BIN)/benzetim
	./$(BIN)/benzetim $(AYAR)

temizle:
	rm -rf $(BIN)
