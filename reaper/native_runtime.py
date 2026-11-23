"""C17 runtime support used by Reaper's native compiler.

The runtime is intentionally small and is emitted only into native programs
that use it. Heap objects are reference counted; strings created by concat
are arena-tracked until the common program cleanup path.
"""

C_RUNTIME = r"""
typedef struct {
    size_t references;
    size_t length;
    size_t capacity;
    int64_t *items;
} RprArray;

typedef struct {
    const char *key;
    int64_t value;
} RprMapInit;

typedef struct {
    char *key;
    int64_t value;
} RprMapEntry;

typedef struct {
    size_t references;
    size_t length;
    size_t capacity;
    RprMapEntry *entries;
} RprMap;

typedef struct RprStringAllocation {
    char *data;
    size_t size;
    struct RprStringAllocation *next;
} RprStringAllocation;

static size_t rpr_heap_bytes = 0;
static RprStringAllocation *rpr_string_allocations = NULL;

static inline void *rpr_heap_alloc(size_t size) {
    const size_t limit = 64U * 1024U * 1024U;
    if (size == 0U) size = 1U;
    if (size > limit - rpr_heap_bytes) {
        (void)rpr_fail("native heap limit exceeded");
        return NULL;
    }
    void *memory = calloc(1U, size);
    if (memory == NULL) {
        (void)rpr_fail("native heap allocation failed");
        return NULL;
    }
    rpr_heap_bytes += size;
    return memory;
}

static inline void rpr_heap_free(void *memory, size_t size) {
    if (memory == NULL) return;
    free(memory);
    if (size <= rpr_heap_bytes) rpr_heap_bytes -= size;
    else rpr_heap_bytes = 0U;
}

static inline char *rpr_string_copy(const char *source) {
    if (source == NULL) {
        (void)rpr_fail("null string value");
        return NULL;
    }
    size_t length = strlen(source);
    if (length > 1000000U) {
        (void)rpr_fail("native string length limit exceeded");
        return NULL;
    }
    char *copy = (char *)rpr_heap_alloc(length + 1U);
    if (copy != NULL) memcpy(copy, source, length + 1U);
    return copy;
}

static inline const char *rpr_string_concat(const char *left, const char *right) {
    if (left == NULL || right == NULL) {
        (void)rpr_fail("cannot concatenate a null string");
        return "";
    }
    size_t left_length = strlen(left);
    size_t right_length = strlen(right);
    if (left_length > 1000000U || right_length > 1000000U ||
        left_length + right_length > 1000000U) {
        (void)rpr_fail("native string length limit exceeded");
        return "";
    }
    size_t size = left_length + right_length + 1U;
    char *joined = (char *)rpr_heap_alloc(size);
    if (joined == NULL) return "";
    memcpy(joined, left, left_length);
    memcpy(joined + left_length, right, right_length + 1U);

    RprStringAllocation *allocation =
        (RprStringAllocation *)rpr_heap_alloc(sizeof *allocation);
    if (allocation == NULL) {
        rpr_heap_free(joined, size);
        return "";
    }
    allocation->data = joined;
    allocation->size = size;
    allocation->next = rpr_string_allocations;
    rpr_string_allocations = allocation;
    return joined;
}

static inline int64_t rpr_string_length(const char *value) {
    if (value == NULL) return rpr_fail("null string value");
    size_t length = strlen(value);
    if (length > INT64_MAX) return rpr_fail("string length exceeds i64");
    return (int64_t)length;
}

static inline void rpr_string_cleanup(void) {
    RprStringAllocation *item = rpr_string_allocations;
    while (item != NULL) {
        RprStringAllocation *next = item->next;
        rpr_heap_free(item->data, item->size);
        rpr_heap_free(item, sizeof *item);
        item = next;
    }
    rpr_string_allocations = NULL;
}

static inline RprArray *rpr_array_from(const int64_t *items, size_t length) {
    if (length > 100000U) {
        (void)rpr_fail("native array item limit exceeded");
        return NULL;
    }
    RprArray *array = (RprArray *)rpr_heap_alloc(sizeof *array);
    if (array == NULL) return NULL;
    array->references = 1U;
    array->length = length;
    array->capacity = length < 4U ? 4U : length;
    array->items = (int64_t *)rpr_heap_alloc(array->capacity * sizeof *array->items);
    if (array->items == NULL) {
        rpr_heap_free(array, sizeof *array);
        return NULL;
    }
    if (length != 0U && items != NULL)
        memcpy(array->items, items, length * sizeof *items);
    return array;
}

static inline RprArray *rpr_array_retain(RprArray *array) {
    if (array != NULL) {
        if (array->references == SIZE_MAX) {
            (void)rpr_fail("native array reference count overflow");
            return NULL;
        }
        ++array->references;
    }
    return array;
}

static inline void rpr_array_release(RprArray *array) {
    if (array == NULL || array->references == 0U) return;
    --array->references;
    if (array->references == 0U) {
        rpr_heap_free(array->items, array->capacity * sizeof *array->items);
        rpr_heap_free(array, sizeof *array);
    }
}

static inline int64_t rpr_array_get_owned(RprArray *array, int64_t index) {
    if (array == NULL) return rpr_fail("cannot index a null array");
    if (index < 0 || (uint64_t)index >= (uint64_t)array->length) {
        rpr_array_release(array);
        return rpr_fail("array index is out of range");
    }
    int64_t value = array->items[(size_t)index];
    rpr_array_release(array);
    return value;
}

static inline int64_t rpr_array_length_owned(RprArray *array) {
    if (array == NULL) return rpr_fail("cannot measure a null array");
    size_t length = array->length;
    rpr_array_release(array);
    if (length > INT64_MAX) return rpr_fail("array length exceeds i64");
    return (int64_t)length;
}

static inline RprArray *rpr_array_clone(const RprArray *source) {
    if (source == NULL) {
        (void)rpr_fail("cannot clone a null array");
        return NULL;
    }
    return rpr_array_from(source->items, source->length);
}

static inline RprArray *rpr_array_push_owned(RprArray *array, int64_t value) {
    if (array == NULL) {
        (void)rpr_fail("cannot append to a null array");
        return NULL;
    }
    if (array->length >= 100000U) {
        rpr_array_release(array);
        (void)rpr_fail("native array item limit exceeded");
        return NULL;
    }
    if (array->references > 1U) {
        RprArray *copy = rpr_array_clone(array);
        rpr_array_release(array);
        array = copy;
        if (array == NULL) return NULL;
    }
    if (array->length == array->capacity) {
        size_t next_capacity = array->capacity < 4U ? 4U : array->capacity * 2U;
        if (next_capacity > 100000U) next_capacity = 100000U;
        int64_t *next_items = (int64_t *)rpr_heap_alloc(next_capacity * sizeof *next_items);
        if (next_items == NULL) {
            rpr_array_release(array);
            return NULL;
        }
        memcpy(next_items, array->items, array->length * sizeof *next_items);
        rpr_heap_free(array->items, array->capacity * sizeof *array->items);
        array->items = next_items;
        array->capacity = next_capacity;
    }
    array->items[array->length++] = value;
    return array;
}

static inline void rpr_array_print_owned(RprArray *array) {
    if (array == NULL) {
        (void)rpr_fail("cannot print a null array");
        return;
    }
    (void)putchar('[');
    for (size_t index = 0U; index < array->length; ++index) {
        if (index != 0U) (void)fputs(", ", stdout);
        (void)printf("%" PRId64, array->items[index]);
    }
    (void)puts("]");
    rpr_array_release(array);
}

static inline RprMap *rpr_map_new(void) {
    RprMap *map = (RprMap *)rpr_heap_alloc(sizeof *map);
    if (map == NULL) return NULL;
    map->references = 1U;
    map->capacity = 4U;
    map->entries = (RprMapEntry *)rpr_heap_alloc(map->capacity * sizeof *map->entries);
    if (map->entries == NULL) {
        rpr_heap_free(map, sizeof *map);
        return NULL;
    }
    return map;
}

static inline RprMap *rpr_map_retain(RprMap *map) {
    if (map != NULL) {
        if (map->references == SIZE_MAX) {
            (void)rpr_fail("native map reference count overflow");
            return NULL;
        }
        ++map->references;
    }
    return map;
}

static inline void rpr_map_release(RprMap *map) {
    if (map == NULL || map->references == 0U) return;
    --map->references;
    if (map->references == 0U) {
        for (size_t index = 0U; index < map->length; ++index)
            rpr_heap_free(map->entries[index].key, strlen(map->entries[index].key) + 1U);
        rpr_heap_free(map->entries, map->capacity * sizeof *map->entries);
        rpr_heap_free(map, sizeof *map);
    }
}

static inline RprMap *rpr_map_clone(const RprMap *source) {
    if (source == NULL) {
        (void)rpr_fail("cannot clone a null map");
        return NULL;
    }
    RprMap *copy = rpr_map_new();
    if (copy == NULL) return NULL;
    for (size_t index = 0U; index < source->length; ++index) {
        char *key = rpr_string_copy(source->entries[index].key);
        if (key == NULL) {
            rpr_map_release(copy);
            return NULL;
        }
        if (copy->length == copy->capacity) {
            size_t next_capacity = copy->capacity * 2U;
            RprMapEntry *next_entries =
                (RprMapEntry *)rpr_heap_alloc(next_capacity * sizeof *next_entries);
            if (next_entries == NULL) {
                rpr_heap_free(key, strlen(key) + 1U);
                rpr_map_release(copy);
                return NULL;
            }
            memcpy(next_entries, copy->entries, copy->length * sizeof *next_entries);
            rpr_heap_free(copy->entries, copy->capacity * sizeof *copy->entries);
            copy->entries = next_entries;
            copy->capacity = next_capacity;
        }
        copy->entries[copy->length++] = (RprMapEntry){key, source->entries[index].value};
    }
    return copy;
}

static inline RprMap *rpr_map_put_owned(RprMap *map, const char *key, int64_t value) {
    if (map == NULL || key == NULL) {
        rpr_map_release(map);
        (void)rpr_fail("map insertion requires a map and a string key");
        return NULL;
    }
    if (map->references > 1U) {
        RprMap *copy = rpr_map_clone(map);
        rpr_map_release(map);
        map = copy;
        if (map == NULL) return NULL;
    }
    for (size_t index = 0U; index < map->length; ++index) {
        if (strcmp(map->entries[index].key, key) == 0) {
            map->entries[index].value = value;
            return map;
        }
    }
    if (map->length >= 100000U) {
        rpr_map_release(map);
        (void)rpr_fail("native map entry limit exceeded");
        return NULL;
    }
    if (map->length == map->capacity) {
        size_t next_capacity = map->capacity * 2U;
        RprMapEntry *next_entries =
            (RprMapEntry *)rpr_heap_alloc(next_capacity * sizeof *next_entries);
        if (next_entries == NULL) {
            rpr_map_release(map);
            return NULL;
        }
        memcpy(next_entries, map->entries, map->length * sizeof *next_entries);
        rpr_heap_free(map->entries, map->capacity * sizeof *map->entries);
        map->entries = next_entries;
        map->capacity = next_capacity;
    }
    char *key_copy = rpr_string_copy(key);
    if (key_copy == NULL) {
        rpr_map_release(map);
        return NULL;
    }
    map->entries[map->length++] = (RprMapEntry){key_copy, value};
    return map;
}

static inline RprMap *rpr_map_from(const RprMapInit *items, size_t count) {
    if (count > 100000U) {
        (void)rpr_fail("native map entry limit exceeded");
        return NULL;
    }
    RprMap *map = rpr_map_new();
    if (map == NULL) return NULL;
    for (size_t index = 0U; index < count; ++index) {
        map = rpr_map_put_owned(map, items[index].key, items[index].value);
        if (map == NULL) return NULL;
    }
    return map;
}

static inline int64_t rpr_map_get_owned(RprMap *map, const char *key) {
    if (map == NULL || key == NULL) {
        rpr_map_release(map);
        return rpr_fail("map lookup requires a map and a string key");
    }
    for (size_t index = 0U; index < map->length; ++index) {
        if (strcmp(map->entries[index].key, key) == 0) {
            int64_t value = map->entries[index].value;
            rpr_map_release(map);
            return value;
        }
    }
    rpr_map_release(map);
    return rpr_fail("dictionary key does not exist");
}

static inline int64_t rpr_map_has_owned(RprMap *map, const char *key) {
    if (map == NULL || key == NULL) {
        rpr_map_release(map);
        return rpr_fail("map membership requires a map and a string key");
    }
    int found = 0;
    for (size_t index = 0U; index < map->length; ++index)
        if (strcmp(map->entries[index].key, key) == 0) found = 1;
    rpr_map_release(map);
    return found;
}

static inline int64_t rpr_map_length_owned(RprMap *map) {
    if (map == NULL) return rpr_fail("cannot measure a null map");
    size_t length = map->length;
    rpr_map_release(map);
    if (length > INT64_MAX) return rpr_fail("map length exceeds i64");
    return (int64_t)length;
}

static inline void rpr_print_quoted(const char *value) {
    (void)putchar('"');
    for (const unsigned char *cursor = (const unsigned char *)value; *cursor; ++cursor) {
        if (*cursor == '"' || *cursor == '\\') {
            (void)putchar('\\');
            (void)putchar(*cursor);
        } else if (*cursor == '\n') {
            (void)fputs("\\n", stdout);
        } else if (*cursor == '\r') {
            (void)fputs("\\r", stdout);
        } else if (*cursor == '\t') {
            (void)fputs("\\t", stdout);
        } else {
            (void)putchar(*cursor);
        }
    }
    (void)putchar('"');
}

static inline void rpr_map_print_owned(RprMap *map) {
    if (map == NULL) {
        (void)rpr_fail("cannot print a null map");
        return;
    }
    (void)putchar('{');
    for (size_t index = 0U; index < map->length; ++index) {
        if (index != 0U) (void)fputs(", ", stdout);
        rpr_print_quoted(map->entries[index].key);
        (void)fputs(": ", stdout);
        (void)printf("%" PRId64, map->entries[index].value);
    }
    (void)puts("}");
    rpr_map_release(map);
}
"""


def render_native_runtime() -> str:
    """Return the C17 aggregate/string helpers embedded by the AOT backend."""
    return C_RUNTIME
