#include "appguard.h"
#include <string.h>

static int vee_valid_context(unsigned level_id, const char *rule_id, const char *object_id)
{
    return level_id >= 1U && level_id <= 666U &&
           rule_id != NULL && rule_id[0] != '\0' &&
           object_id != NULL && object_id[0] != '\0';
}

static vee_decision vee_emit(const vee_guard *guard, unsigned level_id,
                             const char *rule_id, const char *object_id,
                             vee_decision decision, const char *reason)
{
    if (guard != NULL && guard->audit != NULL &&
        vee_valid_context(level_id, rule_id, object_id)) {
        const vee_finding finding = {level_id, rule_id, object_id, decision, reason};
        guard->audit(&finding, guard->audit_context);
    }
    return decision;
}

void vee_guard_init(vee_guard *guard, size_t max_payload_bytes,
                    size_t max_collection_items, size_t max_identifier_bytes,
                    size_t max_path_bytes, vee_audit_callback audit,
                    void *audit_context)
{
    if (guard == NULL) return;
    guard->max_payload_bytes = max_payload_bytes != 0U ? max_payload_bytes : 1024U * 1024U;
    guard->max_collection_items = max_collection_items != 0U ? max_collection_items : 4096U;
    guard->max_identifier_bytes = max_identifier_bytes != 0U ? max_identifier_bytes : 128U;
    guard->max_path_bytes = max_path_bytes != 0U ? max_path_bytes : 1024U;
    guard->audit = audit;
    guard->audit_context = audit_context;
}

vee_decision vee_guard_check_payload(const vee_guard *guard, unsigned level_id,
                                     const char *rule_id, const char *object_id,
                                     size_t actual_bytes)
{
    if (guard == NULL || !vee_valid_context(level_id, rule_id, object_id)) return VEEELZEVUL_DENY;
    if (actual_bytes > guard->max_payload_bytes)
        return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_DENY, "payload byte ceiling exceeded");
    return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_ALLOW, "payload byte ceiling satisfied");
}

vee_decision vee_guard_check_collection(const vee_guard *guard, unsigned level_id,
                                        const char *rule_id, const char *object_id,
                                        size_t actual_items)
{
    if (guard == NULL || !vee_valid_context(level_id, rule_id, object_id)) return VEEELZEVUL_DENY;
    if (actual_items > guard->max_collection_items)
        return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_DEGRADE, "collection item ceiling exceeded");
    return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_ALLOW, "collection item ceiling satisfied");
}

vee_decision vee_guard_check_identifier(const vee_guard *guard, unsigned level_id,
                                        const char *rule_id, const char *object_id,
                                        const char *value)
{
    size_t index, length;
    if (guard == NULL || !vee_valid_context(level_id, rule_id, object_id) || value == NULL) return VEEELZEVUL_DENY;
    length = strlen(value);
    if (length == 0U || length > guard->max_identifier_bytes || value[0] == '.')
        return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_DENY, "identifier length or prefix rejected");
    for (index = 0U; index < length; ++index) {
        const unsigned char ch = (unsigned char)value[index];
        const int allowed =
            (ch >= (unsigned char)'a' && ch <= (unsigned char)'z') ||
            (ch >= (unsigned char)'A' && ch <= (unsigned char)'Z') ||
            (ch >= (unsigned char)'0' && ch <= (unsigned char)'9') ||
            ch == (unsigned char)'_' || ch == (unsigned char)'-' ||
            ch == (unsigned char)'.' || ch == (unsigned char)':';
        if (!allowed)
            return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_DENY, "identifier contains a disallowed byte");
    }
    return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_ALLOW, "identifier allowlist satisfied");
}

vee_decision vee_guard_check_relative_path(const vee_guard *guard, unsigned level_id,
                                           const char *rule_id, const char *object_id,
                                           const char *path)
{
    const char *segment, *cursor;
    size_t length;
    if (guard == NULL || !vee_valid_context(level_id, rule_id, object_id) || path == NULL || path[0] == '\0')
        return VEEELZEVUL_DENY;
    length = strlen(path);
    if (length > guard->max_path_bytes || path[0] == '/' || path[0] == '\\' ||
        strchr(path, '\\') != NULL || strchr(path, ':') != NULL || path[length - 1U] == '/')
        return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_DENY, "path is absolute, malformed or over limit");
    segment = path;
    for (cursor = path; ; ++cursor) {
        const unsigned char ch = (unsigned char)*cursor;
        if (ch != 0U && (ch < 0x20U || ch == 0x7fU))
            return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_DENY, "path contains a control byte");
        if (ch == (unsigned char)'/' || ch == 0U) {
            const size_t segment_length = (size_t)(cursor - segment);
            if (segment_length == 0U ||
                (segment_length == 1U && segment[0] == '.') ||
                (segment_length == 2U && segment[0] == '.' && segment[1] == '.'))
                return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_DENY, "path traversal or empty segment rejected");
            if (ch == 0U) break;
            segment = cursor + 1;
        }
    }
    return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_ALLOW, "relative path boundary satisfied");
}

vee_decision vee_guard_authorize(const vee_guard *guard, unsigned level_id,
                                 const char *rule_id, const char *object_id,
                                 int authorized)
{
    if (guard == NULL || !vee_valid_context(level_id, rule_id, object_id)) return VEEELZEVUL_DENY;
    if (authorized != 1)
        return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_DENY, "explicit authorization was not granted");
    return vee_emit(guard, level_id, rule_id, object_id, VEEELZEVUL_ALLOW, "explicit authorization granted");
}
