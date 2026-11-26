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

    {
        static const uint8_t hmac_key[20] = {
            0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b,
            0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b
        };
        const char *expected_hmac =
            "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7";
        char chain_one[65], chain_two[65], repeated[65];
        assert(reaper_hmac_sha256_buffer(hmac_key, sizeof hmac_key,
            "Hi There", 8u, digest));
        assert(strcmp(digest, expected_hmac) == 0);
        assert(reaper_hmac_sha256_verify(hmac_key, sizeof hmac_key,
            "Hi There", 8u, expected_hmac));
        assert(!reaper_hmac_sha256_verify(hmac_key, sizeof hmac_key,
            "Hi There!", 9u, expected_hmac));

        assert(reaper_audit_chain_next(expected_empty,
            "apply.started", "req-1", "Ivan-VHS/Reaper", "feat/engine",
            "0123456789012345678901234567890123456789", "", "", "started",
            chain_one));
        assert(reaper_audit_chain_next(chain_one,
            "patch.staged", "req-1", "Ivan-VHS/Reaper", "feat/engine",
            "0123456789012345678901234567890123456789", "src/main.rpr",
            expected_abc, "staged", chain_two));
        assert(reaper_audit_chain_next(expected_empty,
            "apply.started", "req-1", "Ivan-VHS/Reaper", "feat/engine",
            "0123456789012345678901234567890123456789", "", "", "started",
            repeated));
        assert(strcmp(chain_one, repeated) == 0);
        assert(strcmp(chain_one, chain_two) != 0);
        assert(!reaper_audit_chain_next("invalid", "event", "request", "repo",
            "branch", "revision", "path", "digest", "details", repeated));
    }

    puts("native SHA-256 tests: SHA-256, HMAC-SHA-256 and audit-chain vectors passed");
    return 0;
}
