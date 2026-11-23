#include "reaper/dabi64.h"
#include <string.h>

static int valid_utf8(const uint8_t *bytes, uint64_t length) {
    uint64_t i = 0u;
    while (i < length) {
        uint8_t first = bytes[i++];
        if (first <= 0x7fu) continue;
        if (first >= 0xc2u && first <= 0xdfu) {
            if (i >= length || (bytes[i++] & 0xc0u) != 0x80u) return 0;
            continue;
        }
        if (first >= 0xe0u && first <= 0xefu) {
            if (i + 1u >= length) return 0;
            uint8_t second = bytes[i++];
            uint8_t third = bytes[i++];
            if ((third & 0xc0u) != 0x80u) return 0;
            if (first == 0xe0u) {
                if (second < 0xa0u || second > 0xbfu) return 0;
            } else if (first == 0xedu) {
                if (second < 0x80u || second > 0x9fu) return 0;
            } else if ((second & 0xc0u) != 0x80u) {
                return 0;
            }
            continue;
        }
        if (first >= 0xf0u && first <= 0xf4u) {
            if (i + 2u >= length) return 0;
            uint8_t second = bytes[i++];
            uint8_t third = bytes[i++];
            uint8_t fourth = bytes[i++];
            if ((third & 0xc0u) != 0x80u || (fourth & 0xc0u) != 0x80u)
                return 0;
            if (first == 0xf0u) {
                if (second < 0x90u || second > 0xbfu) return 0;
            } else if (first == 0xf4u) {
                if (second < 0x80u || second > 0x8fu) return 0;
            } else if ((second & 0xc0u) != 0x80u) {
                return 0;
            }
            continue;
        }
        return 0;
    }
    return 1;
}

uint32_t reaper_dabi64_abi_version(void) {
    return REAPER_DABI64_ABI_VERSION;
}

ReaperDabi64Status reaper_dabi64_validate_host(const ReaperDabi64HostV1 *host) {
    if (host == NULL) return REAPER_DABI64_INVALID_ARGUMENT;
    if (host->abi_version != REAPER_DABI64_ABI_VERSION ||
        host->struct_size < sizeof *host)
        return REAPER_DABI64_ABI_MISMATCH;
    if (host->allocate == NULL || host->release == NULL)
        return REAPER_DABI64_INVALID_ARGUMENT;
    return REAPER_DABI64_OK;
}

ReaperDabi64Status reaper_dabi64_validate_module(const ReaperDabi64ModuleV1 *module) {
    if (module == NULL) return REAPER_DABI64_INVALID_ARGUMENT;
    if (module->abi_version != REAPER_DABI64_ABI_VERSION ||
        module->struct_size < sizeof *module)
        return REAPER_DABI64_ABI_MISMATCH;
    if (module->name == NULL || module->name[0] == '\0' || module->invoke == NULL ||
        module->reserved != 0u)
        return REAPER_DABI64_INVALID_ARGUMENT;
    return REAPER_DABI64_OK;
}

ReaperDabi64Status reaper_dabi64_validate_value(const ReaperDabi64Value *value) {
    if (value == NULL) return REAPER_DABI64_INVALID_ARGUMENT;
    if ((value->flags & ~(uint32_t)(REAPER_DABI64_VALUE_OWNED |
                                    REAPER_DABI64_VALUE_IMMUTABLE)) != 0u)
        return REAPER_DABI64_INVALID_VALUE;
    if (value->kind > REAPER_DABI64_VALUE_HANDLE)
        return REAPER_DABI64_INVALID_VALUE;
    switch (value->kind) {
    case REAPER_DABI64_VALUE_UNIT:
        return (value->payload == 0u && value->length == 0u && value->flags == 0u)
            ? REAPER_DABI64_OK : REAPER_DABI64_INVALID_VALUE;
    case REAPER_DABI64_VALUE_I64:
        return (value->length == 0u && value->flags == 0u)
            ? REAPER_DABI64_OK : REAPER_DABI64_INVALID_VALUE;
    case REAPER_DABI64_VALUE_BOOL:
        return (value->payload <= 1u && value->length == 0u && value->flags == 0u)
            ? REAPER_DABI64_OK : REAPER_DABI64_INVALID_VALUE;
    case REAPER_DABI64_VALUE_UTF8:
    case REAPER_DABI64_VALUE_BYTES:
        if (value->length > REAPER_DABI64_MAX_VALUE_BYTES ||
            (value->length != 0u && value->payload == 0u))
            return REAPER_DABI64_INVALID_VALUE;
        if (value->kind == REAPER_DABI64_VALUE_UTF8 &&
            !valid_utf8((const uint8_t *)(uintptr_t)value->payload, value->length))
            return REAPER_DABI64_INVALID_VALUE;
        return REAPER_DABI64_OK;
    case REAPER_DABI64_VALUE_ARRAY_I64:
        if (value->length > REAPER_DABI64_MAX_ARRAY_ITEMS ||
            (value->length != 0u && value->payload == 0u))
            return REAPER_DABI64_INVALID_VALUE;
        return REAPER_DABI64_OK;
    case REAPER_DABI64_VALUE_HANDLE:
        return value->payload != 0u ? REAPER_DABI64_OK : REAPER_DABI64_INVALID_VALUE;
    default:
        return REAPER_DABI64_INVALID_VALUE;
    }
}

void reaper_dabi64_value_release(const ReaperDabi64HostV1 *host, ReaperDabi64Value *value) {
    if (host == NULL || value == NULL || host->release == NULL) return;
    if ((value->flags & REAPER_DABI64_VALUE_OWNED) != 0u &&
        value->payload != 0u &&
        (value->kind == REAPER_DABI64_VALUE_UTF8 ||
         value->kind == REAPER_DABI64_VALUE_BYTES ||
         value->kind == REAPER_DABI64_VALUE_ARRAY_I64 ||
         value->kind == REAPER_DABI64_VALUE_HANDLE))
        host->release(host->context, (void *)(uintptr_t)value->payload);
    memset(value, 0, sizeof *value);
}

ReaperDabi64Status reaper_dabi64_invoke(
    const ReaperDabi64HostV1 *host,
    const ReaperDabi64ModuleV1 *module,
    const ReaperDabi64Value *arguments,
    uint64_t argument_count,
    ReaperDabi64Value *result
) {
    ReaperDabi64Status status = reaper_dabi64_validate_host(host);
    if (status != REAPER_DABI64_OK) return status;
    status = reaper_dabi64_validate_module(module);
    if (status != REAPER_DABI64_OK) return status;
    if (result == NULL || argument_count > REAPER_DABI64_MAX_ARGUMENTS ||
        (argument_count != 0u && arguments == NULL))
        return REAPER_DABI64_INVALID_ARGUMENT;

    memset(result, 0, sizeof *result);
    for (uint64_t index = 0u; index < argument_count; ++index) {
        status = reaper_dabi64_validate_value(&arguments[index]);
        if (status != REAPER_DABI64_OK) return status;
    }
    status = module->invoke(host, arguments, argument_count, result);
    if (status != REAPER_DABI64_OK) {
        reaper_dabi64_value_release(host, result);
        return status;
    }
    status = reaper_dabi64_validate_value(result);
    if (status != REAPER_DABI64_OK) {
        reaper_dabi64_value_release(host, result);
        return status;
    }
    return REAPER_DABI64_OK;
}
