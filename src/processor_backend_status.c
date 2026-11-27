#include "reaper/processor_backends.h"

const char *reaper_processor_backend_status_name(ReaperProcessorBackendStatus status) {
    switch (status) {
    case REAPER_BACKEND_OK: return "ok";
    case REAPER_BACKEND_INVALID_ARGUMENT: return "invalid-argument";
    case REAPER_BACKEND_LIMIT_EXCEEDED: return "limit-exceeded";
    case REAPER_BACKEND_INVALID_ABI: return "invalid-abi";
    case REAPER_BACKEND_DUPLICATE_SYMBOL: return "duplicate-symbol";
    case REAPER_BACKEND_UNRESOLVED_SYMBOL: return "unresolved-symbol";
    case REAPER_BACKEND_RELOCATION_RANGE: return "relocation-range";
    case REAPER_BACKEND_ILLEGAL_INSTRUCTION: return "illegal-instruction";
    case REAPER_BACKEND_INVALID_MEMORY_ACCESS: return "invalid-memory-access";
    case REAPER_BACKEND_STEP_LIMIT: return "step-limit";
    case REAPER_BACKEND_OUTPUT_TOO_SMALL: return "output-too-small";
    case REAPER_BACKEND_INVALID_NET: return "invalid-net";
    }
    return "unknown";
}
