CC=gcc
CFLAGS=-I.

objects = TLSCipher TLSAnalyzation TLSPerformance TLSAdoption curlGetAllErrorCodes TLSCipherASN
all: $(objects)

$(objects): %: %.c
	$(CC) $(CFLAGS) -Wall -o $@ $< -lcurl