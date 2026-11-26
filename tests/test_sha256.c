#include "reaper/sha256.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    char digest[65];
    const char *expected_empty =
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
    const char *expected_abc =
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    ReaperSha256Context context;
    uint8_t raw[32];

    assert(reaper_sha256_buffer("", 0u, digest));
    assert(strcmp(digest, expected_empty) == 0);
    assert(reaper_sha256_buffer("abc", 3u, digest));
    assert(strcmp(digest, expected_abc) == 0);

    reaper_sha256_init(&context);
    assert(reaper_sha256_update(&context, "a", 1u));
    assert(reaper_sha256_update(&context, "bc", 2u));
    reaper_sha256_final(&context, raw);
    reaper_sha256_hex(raw, digest);
    assert(strcmp(digest, expected_abc) == 0);

    puts("native SHA-256 tests: 3 vectors passed");
    return 0;
}
