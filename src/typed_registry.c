#include "reaper/typed_registry.h"

#include <math.h>
#include <string.h>

#define VALUE_FLAGS ((uint32_t)REAPER_TYPED_VALUE_NULL)
#define ARGUMENT_FLAGS ((uint32_t)REAPER_TYPED_ARGUMENT_OPTIONAL | (uint32_t)REAPER_TYPED_ARGUMENT_NULLABLE)
#define CONSTRAINT_FLAGS ((uint32_t)REAPER_TYPED_CONSTRAINT_MINIMUM | (uint32_t)REAPER_TYPED_CONSTRAINT_MAXIMUM | (uint32_t)REAPER_TYPED_CONSTRAINT_MAX_LENGTH | (uint32_t)REAPER_TYPED_CONSTRAINT_HANDLE_KIND)

static int is_power_of_two(size_t value) {
    return value != 0U && (value & (value - 1U)) == 0U;
}

static int valid_key_part(const char *value) {
    const unsigned char *cursor = (const unsigned char *)value;
    if (value == NULL || *value == '\0') return 0;
    while (*cursor != 0U) {
        const unsigned char ch = *cursor;
        const int valid = (ch >= (unsigned char)'a' && ch <= (unsigned char)'z') ||
            (ch >= (unsigned char)'A' && ch <= (unsigned char)'Z') ||
            (ch >= (unsigned char)'0' && ch <= (unsigned char)'9') ||
            ch == (unsigned char)'_' || ch == (unsigned char)'-' ||
            ch == (unsigned char)'.';
        if (!valid) return 0;
        ++cursor;
    }
    return 1;
}

static uint64_t hash_bytes(uint64_t hash, const unsigned char *bytes, size_t length) {
    for (size_t i = 0U; i < length; ++i) {
        hash ^= (uint64_t)bytes[i];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static uint64_t operation_hash(const char *domain, const char *name, uint16_t abi_major) {
    uint64_t hash = UINT64_C(14695981039346656037);
    const unsigned char separator = 0xffU;
    const unsigned char major_low = (unsigned char)(abi_major & UINT16_C(0xff));
    const unsigned char major_high = (unsigned char)(abi_major >> 8U);
    hash = hash_bytes(hash, (const unsigned char *)domain, strlen(domain));
    hash = hash_bytes(hash, &separator, 1U);
    hash = hash_bytes(hash, (const unsigned char *)name, strlen(name));
    hash = hash_bytes(hash, &separator, 1U);
    hash = hash_bytes(hash, &major_low, 1U);
    hash = hash_bytes(hash, &major_high, 1U);
    return hash;
}

static int key_matches(const ReaperTypedEntry *entry, const char *domain,
                       const char *name, uint16_t abi_major, uint64_t hash) {
    return entry->hash == hash && entry->abi_major == abi_major &&
        strcmp(entry->domain, domain) == 0 && strcmp(entry->name, name) == 0;
}

static int valid_kind(uint32_t kind, int allow_void) {
    if (allow_void && kind == (uint32_t)REAPER_TYPED_VOID) return 1;
    return kind >= (uint32_t)REAPER_TYPED_BOOL &&
        kind <= (uint32_t)REAPER_TYPED_HANDLE;
}

static int utf8_valid(const unsigned char *bytes, size_t length) {
    size_t index = 0U;
    while (index < length) {
        const unsigned char first = bytes[index];
        uint32_t codepoint;
        size_t continuation_count;
        if (first <= 0x7fU) {
            ++index;
            continue;
        }
        if (first >= 0xc2U && first <= 0xdfU) {
            codepoint = (uint32_t)(first & 0x1fU);
            continuation_count = 1U;
        } else if (first >= 0xe0U && first <= 0xefU) {
            codepoint = (uint32_t)(first & 0x0fU);
            continuation_count = 2U;
        } else if (first >= 0xf0U && first <= 0xf4U) {
            codepoint = (uint32_t)(first & 0x07U);
            continuation_count = 3U;
        } else {
            return 0;
        }
        if (continuation_count > length - index - 1U) return 0;
        for (size_t offset = 1U; offset <= continuation_count; ++offset) {
            const unsigned char next = bytes[index + offset];
            if ((next & 0xc0U) != 0x80U) return 0;
            codepoint = (codepoint << 6U) | (uint32_t)(next & 0x3fU);
        }
        if ((continuation_count == 2U && codepoint < 0x800U) ||
            (continuation_count == 3U && codepoint < 0x10000U) ||
            (codepoint >= 0xd800U && codepoint <= 0xdfffU) ||
            codepoint > 0x10ffffU) return 0;
        index += continuation_count + 1U;
    }
    return 1;
}

static int numeric_bound_valid(const ReaperTypedValue *bound, uint32_t kind) {
    return bound->kind == kind && bound->flags == 0U &&
        (kind == (uint32_t)REAPER_TYPED_I64 ||
         kind == (uint32_t)REAPER_TYPED_U64 ||
         kind == (uint32_t)REAPER_TYPED_F64);
}

static int value_leq(const ReaperTypedValue *left, const ReaperTypedValue *right) {
    switch (left->kind) {
        case REAPER_TYPED_I64: return left->as.i64 <= right->as.i64;
        case REAPER_TYPED_U64: return left->as.u64 <= right->as.u64;
        case REAPER_TYPED_F64: return left->as.f64 <= right->as.f64;
        default: return 0;
    }
}

static ReaperTypedStatus validate_spec(const ReaperTypedArgumentSpec *spec, int is_result) {
    if (spec == NULL || !valid_kind(spec->kind, is_result) ||
        (spec->flags & ~ARGUMENT_FLAGS) != 0U ||
        (spec->constraints & ~CONSTRAINT_FLAGS) != 0U)
        return REAPER_TYPED_INVALID_ARGUMENT;
    if (is_result && (spec->flags & REAPER_TYPED_ARGUMENT_OPTIONAL) != 0U)
        return REAPER_TYPED_INVALID_ARGUMENT;
    if (spec->kind == (uint32_t)REAPER_TYPED_VOID) {
        if (!is_result || spec->flags != 0U || spec->constraints != 0U)
            return REAPER_TYPED_INVALID_ARGUMENT;
        return REAPER_TYPED_OK;
    }
    if ((spec->constraints & (REAPER_TYPED_CONSTRAINT_MINIMUM |
                              REAPER_TYPED_CONSTRAINT_MAXIMUM)) != 0U) {
        if (spec->kind != (uint32_t)REAPER_TYPED_I64 &&
            spec->kind != (uint32_t)REAPER_TYPED_U64 &&
            spec->kind != (uint32_t)REAPER_TYPED_F64)
            return REAPER_TYPED_INVALID_ARGUMENT;
        if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MINIMUM) != 0U &&
            (!numeric_bound_valid(&spec->minimum, spec->kind) ||
             (spec->kind == (uint32_t)REAPER_TYPED_F64 &&
              !isfinite(spec->minimum.as.f64)))) return REAPER_TYPED_INVALID_ARGUMENT;
        if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MAXIMUM) != 0U &&
            (!numeric_bound_valid(&spec->maximum, spec->kind) ||
             (spec->kind == (uint32_t)REAPER_TYPED_F64 &&
              !isfinite(spec->maximum.as.f64)))) return REAPER_TYPED_INVALID_ARGUMENT;
        if ((spec->constraints & (REAPER_TYPED_CONSTRAINT_MINIMUM |
                                  REAPER_TYPED_CONSTRAINT_MAXIMUM)) ==
            (REAPER_TYPED_CONSTRAINT_MINIMUM | REAPER_TYPED_CONSTRAINT_MAXIMUM) &&
            !value_leq(&spec->minimum, &spec->maximum))
            return REAPER_TYPED_INVALID_ARGUMENT;
    }
    if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MAX_LENGTH) != 0U &&
        spec->kind != (uint32_t)REAPER_TYPED_UTF8 &&
        spec->kind != (uint32_t)REAPER_TYPED_BYTES)
        return REAPER_TYPED_INVALID_ARGUMENT;
    if ((spec->constraints & REAPER_TYPED_CONSTRAINT_HANDLE_KIND) != 0U &&
        (spec->kind != (uint32_t)REAPER_TYPED_HANDLE ||
         spec->expected_handle_kind == 0U))
        return REAPER_TYPED_INVALID_ARGUMENT;
    if ((spec->constraints & REAPER_TYPED_CONSTRAINT_HANDLE_KIND) == 0U &&
        spec->expected_handle_kind != 0U) return REAPER_TYPED_INVALID_ARGUMENT;
    if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MAX_LENGTH) == 0U &&
        spec->max_length != 0U) return REAPER_TYPED_INVALID_ARGUMENT;
    if ((spec->minimum.flags & ~VALUE_FLAGS) != 0U ||
        (spec->maximum.flags & ~VALUE_FLAGS) != 0U)
        return REAPER_TYPED_INVALID_ARGUMENT;
    return REAPER_TYPED_OK;
}

static ReaperTypedStatus validate_value(const ReaperTypedValue *value,
                                        const ReaperTypedArgumentSpec *spec) {
    if (value == NULL || spec == NULL || value->kind != spec->kind ||
        (value->flags & ~VALUE_FLAGS) != 0U)
        return REAPER_TYPED_TYPE_MISMATCH;
    if ((value->flags & REAPER_TYPED_VALUE_NULL) != 0U)
        return (spec->flags & REAPER_TYPED_ARGUMENT_NULLABLE) != 0U ?
            REAPER_TYPED_OK : REAPER_TYPED_TYPE_MISMATCH;
    switch (spec->kind) {
        case REAPER_TYPED_BOOL:
            if (value->as.boolean > 1U) return REAPER_TYPED_TYPE_MISMATCH;
            break;
        case REAPER_TYPED_I64:
            if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MINIMUM) != 0U &&
                value->as.i64 < spec->minimum.as.i64) return REAPER_TYPED_OUT_OF_RANGE;
            if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MAXIMUM) != 0U &&
                value->as.i64 > spec->maximum.as.i64) return REAPER_TYPED_OUT_OF_RANGE;
            break;
        case REAPER_TYPED_U64:
            if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MINIMUM) != 0U &&
                value->as.u64 < spec->minimum.as.u64) return REAPER_TYPED_OUT_OF_RANGE;
            if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MAXIMUM) != 0U &&
                value->as.u64 > spec->maximum.as.u64) return REAPER_TYPED_OUT_OF_RANGE;
            break;
        case REAPER_TYPED_F64:
            if (!isfinite(value->as.f64)) return REAPER_TYPED_TYPE_MISMATCH;
            if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MINIMUM) != 0U &&
                value->as.f64 < spec->minimum.as.f64) return REAPER_TYPED_OUT_OF_RANGE;
            if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MAXIMUM) != 0U &&
                value->as.f64 > spec->maximum.as.f64) return REAPER_TYPED_OUT_OF_RANGE;
            break;
        case REAPER_TYPED_UTF8:
            if ((value->as.text.data == NULL && value->as.text.length != 0U) ||
                !utf8_valid((const unsigned char *)value->as.text.data,
                            value->as.text.length)) return REAPER_TYPED_TYPE_MISMATCH;
            if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MAX_LENGTH) != 0U &&
                value->as.text.length > spec->max_length) return REAPER_TYPED_OUT_OF_RANGE;
            break;
        case REAPER_TYPED_BYTES:
            if (value->as.bytes.data == NULL && value->as.bytes.length != 0U)
                return REAPER_TYPED_TYPE_MISMATCH;
            if ((spec->constraints & REAPER_TYPED_CONSTRAINT_MAX_LENGTH) != 0U &&
                value->as.bytes.length > spec->max_length) return REAPER_TYPED_OUT_OF_RANGE;
            break;
        case REAPER_TYPED_HANDLE:
            if (value->as.handle.id == 0U ||
                ((spec->constraints & REAPER_TYPED_CONSTRAINT_HANDLE_KIND) != 0U &&
                 value->as.handle.kind != spec->expected_handle_kind))
                return REAPER_TYPED_TYPE_MISMATCH;
            break;
        default:
            return REAPER_TYPED_TYPE_MISMATCH;
    }
    return REAPER_TYPED_OK;
}

ReaperTypedStatus reaper_typed_registry_init(
    ReaperTypedRegistry *registry,
    ReaperTypedEntry *entries,
    size_t entry_capacity,
    size_t *buckets,
    size_t bucket_capacity,
    char *string_storage,
    size_t string_capacity,
    ReaperTypedArgumentSpec *argument_storage,
    size_t argument_capacity) {
    if (registry == NULL || entries == NULL || buckets == NULL ||
        entry_capacity == 0U || entry_capacity > SIZE_MAX / 2U ||
        !is_power_of_two(bucket_capacity) ||
        bucket_capacity < entry_capacity * 2U ||
        bucket_capacity > SIZE_MAX / sizeof(size_t) ||
        entry_capacity > SIZE_MAX / sizeof(ReaperTypedEntry) ||
        (string_capacity > 0U && string_storage == NULL) ||
        (argument_capacity > 0U && argument_storage == NULL) ||
        argument_capacity > SIZE_MAX / sizeof(ReaperTypedArgumentSpec))
        return REAPER_TYPED_INVALID_ARGUMENT;
    memset(buckets, 0, bucket_capacity * sizeof(size_t));
    memset(entries, 0, entry_capacity * sizeof(ReaperTypedEntry));
    registry->entries = entries;
    registry->entry_capacity = entry_capacity;
    registry->count = 0U;
    registry->buckets = buckets;
    registry->bucket_capacity = bucket_capacity;
    registry->string_storage = string_storage;
    registry->string_capacity = string_capacity;
    registry->string_used = 0U;
    registry->argument_storage = argument_storage;
    registry->argument_capacity = argument_capacity;
    registry->argument_used = 0U;
    registry->abi_version = REAPER_TYPED_REGISTRY_ABI_VERSION;
    registry->sealed = 0U;
    return REAPER_TYPED_OK;
}

ReaperTypedStatus reaper_typed_registry_register(
    ReaperTypedRegistry *registry,
    const ReaperTypedOperationSpec *operation) {
    const size_t domain_length = operation != NULL && operation->domain != NULL ?
        strlen(operation->domain) : 0U;
    const size_t name_length = operation != NULL && operation->name != NULL ?
        strlen(operation->name) : 0U;
    size_t required_string_bytes;
    size_t min_arity = 0U;
    int optional_seen = 0;
    uint64_t hash;
    size_t bucket;
    size_t target_bucket = SIZE_MAX;
    if (registry == NULL || registry->abi_version != REAPER_TYPED_REGISTRY_ABI_VERSION ||
        operation == NULL || !valid_key_part(operation->domain) ||
        !valid_key_part(operation->name) || operation->abi_major == 0U ||
        operation->argument_count > REAPER_TYPED_MAX_ARGUMENTS ||
        (operation->argument_count > 0U && operation->arguments == NULL))
        return REAPER_TYPED_INVALID_ARGUMENT;
    if (registry->sealed != 0U) return REAPER_TYPED_SEALED;
    if (registry->count >= registry->entry_capacity) return REAPER_TYPED_FULL;
    if (name_length > SIZE_MAX - 2U ||
        domain_length > SIZE_MAX - name_length - 2U)
        return REAPER_TYPED_OUT_OF_RANGE;
    required_string_bytes = domain_length + name_length + 2U;
    if (registry->string_used > registry->string_capacity ||
        required_string_bytes > registry->string_capacity - registry->string_used ||
        registry->argument_used > registry->argument_capacity ||
        operation->argument_count > registry->argument_capacity - registry->argument_used)
        return REAPER_TYPED_OUT_OF_RANGE;
    if (operation->argument_count > 0U && registry->argument_storage == NULL)
        return REAPER_TYPED_OUT_OF_RANGE;
    if (validate_spec(&operation->result, 1) != REAPER_TYPED_OK)
        return REAPER_TYPED_INVALID_ARGUMENT;
    for (size_t i = 0U; i < operation->argument_count; ++i) {
        const ReaperTypedArgumentSpec *argument = &operation->arguments[i];
        if (validate_spec(argument, 0) != REAPER_TYPED_OK)
            return REAPER_TYPED_INVALID_ARGUMENT;
        if ((argument->flags & REAPER_TYPED_ARGUMENT_OPTIONAL) != 0U) {
            optional_seen = 1;
        } else {
            if (optional_seen != 0) return REAPER_TYPED_INVALID_ARGUMENT;
            ++min_arity;
        }
    }
    hash = operation_hash(operation->domain, operation->name, operation->abi_major);
    bucket = (size_t)(hash & (uint64_t)(registry->bucket_capacity - 1U));
    for (size_t probe = 0U; probe < registry->bucket_capacity; ++probe) {
        const size_t encoded_slot = registry->buckets[bucket];
        if (encoded_slot == 0U) {
            target_bucket = bucket;
            break;
        }
        if (key_matches(&registry->entries[encoded_slot - 1U], operation->domain,
                        operation->name, operation->abi_major, hash))
            return REAPER_TYPED_DUPLICATE;
        bucket = (bucket + 1U) & (registry->bucket_capacity - 1U);
    }
    if (target_bucket == SIZE_MAX) return REAPER_TYPED_FULL;

    {
        ReaperTypedEntry *entry = &registry->entries[registry->count];
        char *domain_copy = registry->string_storage + registry->string_used;
        char *name_copy = domain_copy + domain_length + 1U;
        if (domain_length > 0U) memcpy(domain_copy, operation->domain, domain_length);
        domain_copy[domain_length] = '\0';
        if (name_length > 0U) memcpy(name_copy, operation->name, name_length);
        name_copy[name_length] = '\0';
        if (operation->argument_count > 0U) {
            ReaperTypedArgumentSpec *argument_copy =
                &registry->argument_storage[registry->argument_used];
            memcpy(argument_copy, operation->arguments,
                   operation->argument_count * sizeof(ReaperTypedArgumentSpec));
            entry->arguments = argument_copy;
        } else {
            entry->arguments = NULL;
        }
        entry->hash = hash;
        entry->domain = domain_copy;
        entry->name = name_copy;
        entry->abi_major = operation->abi_major;
        entry->abi_minor = operation->abi_minor;
        entry->required_capabilities = operation->required_capabilities;
        entry->argument_count = operation->argument_count;
        entry->min_arity = min_arity;
        entry->result = operation->result;
        entry->handler = operation->handler;
        entry->context = operation->context;
        registry->buckets[target_bucket] = registry->count + 1U;
        registry->string_used += required_string_bytes;
        registry->argument_used += operation->argument_count;
        ++registry->count;
    }
    return REAPER_TYPED_OK;
}

const ReaperTypedEntry *reaper_typed_registry_find(
    const ReaperTypedRegistry *registry,
    const char *domain,
    const char *name,
    uint16_t abi_major) {
    uint64_t hash;
    size_t bucket;
    if (registry == NULL || registry->abi_version != REAPER_TYPED_REGISTRY_ABI_VERSION ||
        !valid_key_part(domain) || !valid_key_part(name) || abi_major == 0U ||
        registry->bucket_capacity == 0U) return NULL;
    hash = operation_hash(domain, name, abi_major);
    bucket = (size_t)(hash & (uint64_t)(registry->bucket_capacity - 1U));
    for (size_t probe = 0U; probe < registry->bucket_capacity; ++probe) {
        const size_t encoded_slot = registry->buckets[bucket];
        if (encoded_slot == 0U) return NULL;
        if (encoded_slot > registry->count) return NULL;
        if (key_matches(&registry->entries[encoded_slot - 1U], domain, name,
                        abi_major, hash))
            return &registry->entries[encoded_slot - 1U];
        bucket = (bucket + 1U) & (registry->bucket_capacity - 1U);
    }
    return NULL;
}

ReaperTypedStatus reaper_typed_registry_invoke(
    const ReaperTypedRegistry *registry,
    const char *domain,
    const char *name,
    uint16_t abi_major,
    uint16_t minimum_abi_minor,
    uint64_t granted_capabilities,
    const ReaperTypedValue *arguments,
    size_t argument_count,
    ReaperTypedValue *result) {
    const ReaperTypedEntry *entry =
        reaper_typed_registry_find(registry, domain, name, abi_major);
    ReaperTypedValue produced;
    ReaperTypedStatus status;
    if (entry == NULL) return REAPER_TYPED_NOT_FOUND;
    if (entry->abi_minor < minimum_abi_minor) return REAPER_TYPED_ABI_MISMATCH;
    if ((entry->required_capabilities & ~granted_capabilities) != 0U)
        return REAPER_TYPED_ACCESS_DENIED;
    if (argument_count < entry->min_arity || argument_count > entry->argument_count ||
        (argument_count > 0U && arguments == NULL))
        return REAPER_TYPED_ARITY_MISMATCH;
    for (size_t i = 0U; i < argument_count; ++i) {
        status = validate_value(&arguments[i], &entry->arguments[i]);
        if (status != REAPER_TYPED_OK) return status;
    }
    if (entry->handler == NULL) return REAPER_TYPED_UNIMPLEMENTED;
    if (entry->result.kind != (uint32_t)REAPER_TYPED_VOID && result == NULL)
        return REAPER_TYPED_INVALID_ARGUMENT;
    memset(&produced, 0, sizeof(produced));
    produced.kind = entry->result.kind;
    status = entry->handler(entry->context, arguments, argument_count, &produced);
    if (status != REAPER_TYPED_OK) {
        return status <= REAPER_TYPED_INVALID_ARGUMENT &&
            status >= REAPER_TYPED_OUT_OF_RANGE ? status : REAPER_TYPED_HANDLER_ERROR;
    }
    if (entry->result.kind == (uint32_t)REAPER_TYPED_VOID) {
        if (result != NULL) {
            memset(result, 0, sizeof(*result));
            result->kind = (uint32_t)REAPER_TYPED_VOID;
        }
        return REAPER_TYPED_OK;
    }
    status = validate_value(&produced, &entry->result);
    if (status != REAPER_TYPED_OK) return status;
    *result = produced;
    return REAPER_TYPED_OK;
}

ReaperTypedStatus reaper_typed_registry_seal(ReaperTypedRegistry *registry) {
    if (registry == NULL || registry->abi_version != REAPER_TYPED_REGISTRY_ABI_VERSION)
        return REAPER_TYPED_INVALID_ARGUMENT;
    registry->sealed = 1U;
    return REAPER_TYPED_OK;
}

size_t reaper_typed_registry_count(const ReaperTypedRegistry *registry) {
    return registry == NULL || registry->abi_version != REAPER_TYPED_REGISTRY_ABI_VERSION ?
        0U : registry->count;
}

size_t reaper_typed_registry_capacity(const ReaperTypedRegistry *registry) {
    return registry == NULL || registry->abi_version != REAPER_TYPED_REGISTRY_ABI_VERSION ?
        0U : registry->entry_capacity;
}

const char *reaper_typed_status_name(ReaperTypedStatus status) {
    switch (status) {
        case REAPER_TYPED_OK: return "ok";
        case REAPER_TYPED_INVALID_ARGUMENT: return "invalid_argument";
        case REAPER_TYPED_NOT_FOUND: return "not_found";
        case REAPER_TYPED_DUPLICATE: return "duplicate";
        case REAPER_TYPED_FULL: return "full";
        case REAPER_TYPED_TYPE_MISMATCH: return "type_mismatch";
        case REAPER_TYPED_ARITY_MISMATCH: return "arity_mismatch";
        case REAPER_TYPED_ACCESS_DENIED: return "access_denied";
        case REAPER_TYPED_UNIMPLEMENTED: return "unimplemented";
        case REAPER_TYPED_ABI_MISMATCH: return "abi_mismatch";
        case REAPER_TYPED_HANDLER_ERROR: return "handler_error";
        case REAPER_TYPED_SEALED: return "sealed";
        case REAPER_TYPED_OUT_OF_RANGE: return "out_of_range";
        default: return "unknown_status";
    }
}
