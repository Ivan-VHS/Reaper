#include "reaper/architecture.h"

#include <stdio.h>
#include <string.h>

#define CONCEPT(id_value, layer_value, key_value, english, russian, meaning) \
    { id_value, layer_value, key_value, english, russian, meaning }

static const ReaperArchitectureLayerInfo LAYERS[] = {
    { REAPER_ARCH_LAYER_FOUNDATION,
      "foundation", "Structural foundation", "Структурный фундамент",
      "Owns the stable structure, shared base layers and extension points." },
    { REAPER_ARCH_LAYER_PLATFORM_EXECUTION,
      "platform-execution", "Platform and execution", "Платформа и выполнение",
      "Defines the host, target platform and bounded execution responsibilities." },
    { REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS,
      "toolchain-assets", "Toolchain and reusable assets", "Инструментарий и артефакты",
      "Groups libraries, packages, tools, stacks and integration adapters." },
    { REAPER_ARCH_LAYER_DESIGN_MODELS,
      "design-models", "Design and models", "Проектирование и модели",
      "Captures context, domain models, patterns and engineering methods." },
    { REAPER_ARCH_LAYER_COMPOSITION,
      "composition", "System composition", "Композиция системы",
      "Describes how systems are decomposed into bounded implementation units." },
    { REAPER_ARCH_LAYER_CONTRACTS,
      "contracts", "Contracts and specifications", "Контракты и спецификации",
      "Defines public boundaries, interaction rules and machine-readable schemas." },
    { REAPER_ARCH_LAYER_TOPOLOGY,
      "topology", "Topology and boundaries", "Топология и границы",
      "Models relationships, placement, boundaries and protected perimeters." },
    { REAPER_ARCH_LAYER_WORKSPACE,
      "workspace", "Workspace and reference points", "Рабочая область и опоры",
      "Defines the developer work area and stable reference baselines." },
    { REAPER_ARCH_LAYER_HARDWARE_INTEGRATION,
      "hardware-integration", "Hardware/software integration", "Аппаратно-программная интеграция",
      "Owns the explicit boundary between hardware, host adapters and software." }
};

static const ReaperArchitectureConceptInfo CONCEPTS[] = {
    CONCEPT(REAPER_ARCH_CONCEPT_FRAMEWORK_FRAME, REAPER_ARCH_LAYER_FOUNDATION, "framework-frame", "Framework frame", "Каркас", "The structural frame that fixes the main parts and their allowed relationships."),
    CONCEPT(REAPER_ARCH_CONCEPT_PLATFORM, REAPER_ARCH_LAYER_PLATFORM_EXECUTION, "platform", "Platform", "Платформа", "The declared target: operating system, processor, ABI and supported host services."),
    CONCEPT(REAPER_ARCH_CONCEPT_ENVIRONMENT, REAPER_ARCH_LAYER_PLATFORM_EXECUTION, "environment", "Environment", "Среда", "The configured conditions and resources in which a tool or program operates."),
    CONCEPT(REAPER_ARCH_CONCEPT_INFRASTRUCTURE, REAPER_ARCH_LAYER_PLATFORM_EXECUTION, "infrastructure", "Infrastructure", "Инфраструктура", "Shared services, storage, build capacity and operational support."),
    CONCEPT(REAPER_ARCH_CONCEPT_ARCHITECTURE, REAPER_ARCH_LAYER_FOUNDATION, "architecture", "Architecture", "Архитектура", "The governing decomposition, ownership boundaries and dependency direction."),
    CONCEPT(REAPER_ARCH_CONCEPT_BASIS, REAPER_ARCH_LAYER_FOUNDATION, "basis", "Basis", "Базис", "The smallest agreed set of primitives on which higher-level facilities rely."),
    CONCEPT(REAPER_ARCH_CONCEPT_BASE, REAPER_ARCH_LAYER_FOUNDATION, "base", "Base", "Основа", "The stable starting implementation shared by dependent capabilities."),
    CONCEPT(REAPER_ARCH_CONCEPT_FOUNDATION, REAPER_ARCH_LAYER_FOUNDATION, "foundation", "Foundation", "Фундамент", "The invariants and contracts that must hold before extensions are added."),
    CONCEPT(REAPER_ARCH_CONCEPT_SKELETON, REAPER_ARCH_LAYER_FOUNDATION, "skeleton", "Skeleton", "Остов", "The minimal mandatory shape of a complete system."),
    CONCEPT(REAPER_ARCH_CONCEPT_BACKBONE, REAPER_ARCH_LAYER_FOUNDATION, "backbone", "Backbone", "Костяк", "The essential components that preserve the system's primary flow."),
    CONCEPT(REAPER_ARCH_CONCEPT_STRUCTURE, REAPER_ARCH_LAYER_FOUNDATION, "structure", "Structure", "Структура", "The explicit arrangement of parts and their relationships."),
    CONCEPT(REAPER_ARCH_CONCEPT_CONSTRUCTION, REAPER_ARCH_LAYER_FOUNDATION, "construction", "Construction", "Конструкция", "The concrete assembly of implementation units into a working whole."),
    CONCEPT(REAPER_ARCH_CONCEPT_ECOSYSTEM, REAPER_ARCH_LAYER_FOUNDATION, "ecosystem", "Ecosystem", "Экосистема", "The governed set of repositories, tools, packages and integrations around Reaper."),
    CONCEPT(REAPER_ARCH_CONCEPT_EXTENSION_LAYER, REAPER_ARCH_LAYER_FOUNDATION, "extension-layer", "Extension layer", "Надстройка", "A higher-level capability that extends the foundation without owning it."),
    CONCEPT(REAPER_ARCH_CONCEPT_SHELL, REAPER_ARCH_LAYER_FOUNDATION, "shell", "Shell", "Оболочка", "A user-facing or integration-facing surface over stable internal contracts."),
    CONCEPT(REAPER_ARCH_CONCEPT_RUNTIME, REAPER_ARCH_LAYER_PLATFORM_EXECUTION, "runtime", "Runtime", "Рантайм", "The services responsible for program lifecycle, execution and managed resources."),
    CONCEPT(REAPER_ARCH_CONCEPT_EXECUTION_ENVIRONMENT, REAPER_ARCH_LAYER_PLATFORM_EXECUTION, "execution-environment", "Execution environment", "Среда выполнения", "The concrete process state, configuration, quotas and capabilities for one run."),
    CONCEPT(REAPER_ARCH_CONCEPT_ENGINE, REAPER_ARCH_LAYER_PLATFORM_EXECUTION, "engine", "Engine", "Движок", "A replaceable executor such as an interpreter, bytecode VM or native backend."),
    CONCEPT(REAPER_ARCH_CONCEPT_KERNEL, REAPER_ARCH_LAYER_PLATFORM_EXECUTION, "kernel", "Kernel", "Ядро", "The small trusted core that coordinates critical resources and core services."),
    CONCEPT(REAPER_ARCH_CONCEPT_LIBRARY, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "library", "Library", "Библиотека", "Reusable implementation units with callable, documented interfaces."),
    CONCEPT(REAPER_ARCH_CONCEPT_TOOLSET, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "toolset", "Toolset", "Набор инструментов", "A related collection of tools used to complete a defined workflow."),
    CONCEPT(REAPER_ARCH_CONCEPT_TOOLING, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "tooling", "Tooling", "Инструментарий", "Compiler, formatter, debugger, test and build tools with explicit inputs and outputs."),
    CONCEPT(REAPER_ARCH_CONCEPT_TOOLKIT, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "toolkit", "Toolkit", "Тулкит", "An integrated reusable collection of libraries and tools for one task domain."),
    CONCEPT(REAPER_ARCH_CONCEPT_PACKAGE, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "package", "Package", "Пакет", "A versioned, identifiable and distributable unit with declared dependencies."),
    CONCEPT(REAPER_ARCH_CONCEPT_STACK, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "stack", "Stack", "Стек", "An ordered set of layers whose compatibility is checked as a whole."),
    CONCEPT(REAPER_ARCH_CONCEPT_TECHNOLOGY_STACK, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "technology-stack", "Technology stack", "Технологический стек", "The selected language, compiler, runtime, platform and integration technologies."),
    CONCEPT(REAPER_ARCH_CONCEPT_TEMPLATE, REAPER_ARCH_LAYER_FOUNDATION, "template", "Template", "Шаблон", "A parameterized source model for creating consistent projects or modules."),
    CONCEPT(REAPER_ARCH_CONCEPT_SKELETON_TEMPLATE, REAPER_ARCH_LAYER_FOUNDATION, "skeleton-template", "Skeleton template", "Скелет", "A minimal project layout that gives a new unit its required files and boundaries."),
    CONCEPT(REAPER_ARCH_CONCEPT_BOILERPLATE, REAPER_ARCH_LAYER_FOUNDATION, "boilerplate", "Boilerplate", "Бойлерплейт", "Generated or copied repetitive source that should remain small and auditable."),
    CONCEPT(REAPER_ARCH_CONCEPT_BASE_LAYER, REAPER_ARCH_LAYER_FOUNDATION, "base-layer", "Base layer", "Базовый слой", "The lowest shared software layer exposed to higher layers through a narrow contract."),
    CONCEPT(REAPER_ARCH_CONCEPT_MIDDLE_LAYER, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "middle-layer", "Middle layer", "Прослойка", "A bounded translation or coordination layer between two otherwise separate layers."),
    CONCEPT(REAPER_ARCH_CONCEPT_MIDDLEWARE, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "middleware", "Middleware", "Мидлвар", "A component that processes requests or events between producers and consumers."),
    CONCEPT(REAPER_ARCH_CONCEPT_GLUE_SOFTWARE, REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS, "glue-software", "Glue software", "Связующее ПО", "Adapters and orchestration code that connect independent components without merging ownership."),
    CONCEPT(REAPER_ARCH_CONCEPT_CONTAINER, REAPER_ARCH_LAYER_PLATFORM_EXECUTION, "container", "Container", "Контейнер", "A bounded packaging or isolation unit with explicit resource and trust limits."),
    CONCEPT(REAPER_ARCH_CONCEPT_HOST, REAPER_ARCH_LAYER_PLATFORM_EXECUTION, "host", "Host", "Хост", "The process or operating system that supplies services through an explicit host ABI."),
    CONCEPT(REAPER_ARCH_CONCEPT_CONTEXT, REAPER_ARCH_LAYER_DESIGN_MODELS, "context", "Context", "Контекст", "The scoped configuration, identity, state and capabilities that affect an operation."),
    CONCEPT(REAPER_ARCH_CONCEPT_MODEL, REAPER_ARCH_LAYER_DESIGN_MODELS, "model", "Model", "Модель", "A formal representation of a domain, system state or transformation."),
    CONCEPT(REAPER_ARCH_CONCEPT_PATTERN, REAPER_ARCH_LAYER_DESIGN_MODELS, "pattern", "Pattern", "Паттерн", "A reusable solution with stated applicability and trade-offs."),
    CONCEPT(REAPER_ARCH_CONCEPT_PARADIGM, REAPER_ARCH_LAYER_DESIGN_MODELS, "paradigm", "Paradigm", "Парадигма", "The coherent semantic rules that shape how programs and tools are designed."),
    CONCEPT(REAPER_ARCH_CONCEPT_CONCEPT, REAPER_ARCH_LAYER_DESIGN_MODELS, "concept", "Concept", "Концепция", "A named design idea with a defined scope and consequences."),
    CONCEPT(REAPER_ARCH_CONCEPT_METHODOLOGY, REAPER_ARCH_LAYER_DESIGN_MODELS, "methodology", "Methodology", "Методология", "A repeatable process for planning, implementation, review and evidence collection."),
    CONCEPT(REAPER_ARCH_CONCEPT_APPROACH, REAPER_ARCH_LAYER_DESIGN_MODELS, "approach", "Approach", "Подход", "A selected practical strategy for solving a bounded engineering problem."),
    CONCEPT(REAPER_ARCH_CONCEPT_SYSTEM, REAPER_ARCH_LAYER_COMPOSITION, "system", "System", "Система", "A complete unit with defined responsibilities, interfaces and observable behavior."),
    CONCEPT(REAPER_ARCH_CONCEPT_SUBSYSTEM, REAPER_ARCH_LAYER_COMPOSITION, "subsystem", "Subsystem", "Подсистема", "A separately bounded part of a system with a narrow internal contract."),
    CONCEPT(REAPER_ARCH_CONCEPT_MODULE, REAPER_ARCH_LAYER_COMPOSITION, "module", "Module", "Модуль", "A cohesive unit with explicit exports, dependencies and lifecycle."),
    CONCEPT(REAPER_ARCH_CONCEPT_COMPONENT, REAPER_ARCH_LAYER_COMPOSITION, "component", "Component", "Компонент", "An implementation unit that owns one clearly stated responsibility."),
    CONCEPT(REAPER_ARCH_CONCEPT_BLOCK, REAPER_ARCH_LAYER_COMPOSITION, "block", "Block", "Блок", "A small composable unit of data, behavior or transformation."),
    CONCEPT(REAPER_ARCH_CONCEPT_NODE, REAPER_ARCH_LAYER_COMPOSITION, "node", "Node", "Узел", "A graph participant with typed incoming and outgoing relationships."),
    CONCEPT(REAPER_ARCH_CONCEPT_INTERFACE, REAPER_ARCH_LAYER_CONTRACTS, "interface", "Interface", "Интерфейс", "The public operations and data shape visible across a component boundary."),
    CONCEPT(REAPER_ARCH_CONCEPT_PROTOCOL, REAPER_ARCH_LAYER_CONTRACTS, "protocol", "Protocol", "Протокол", "The ordered interaction and state-transition rules shared by participants."),
    CONCEPT(REAPER_ARCH_CONCEPT_STANDARD, REAPER_ARCH_LAYER_CONTRACTS, "standard", "Standard", "Стандарт", "A normative compatibility target with explicit version and conformance rules."),
    CONCEPT(REAPER_ARCH_CONCEPT_POLICY, REAPER_ARCH_LAYER_CONTRACTS, "policy", "Policy", "Регламент", "A mandatory governance or operational rule with an owner and enforcement point."),
    CONCEPT(REAPER_ARCH_CONCEPT_SPECIFICATION, REAPER_ARCH_LAYER_CONTRACTS, "specification", "Specification", "Спецификация", "A testable statement of required behavior, limits and failure cases."),
    CONCEPT(REAPER_ARCH_CONCEPT_SCHEMA, REAPER_ARCH_LAYER_CONTRACTS, "schema", "Schema", "Схема", "A machine-readable shape and validation contract for structured data."),
    CONCEPT(REAPER_ARCH_CONCEPT_MATRIX, REAPER_ARCH_LAYER_TOPOLOGY, "matrix", "Matrix", "Матрица", "A multidimensional relation table used to compare coverage and compatibility."),
    CONCEPT(REAPER_ARCH_CONCEPT_GRID, REAPER_ARCH_LAYER_TOPOLOGY, "grid", "Grid", "Сетка", "A regular arrangement used to partition or index system elements."),
    CONCEPT(REAPER_ARCH_CONCEPT_BOUNDARY, REAPER_ARCH_LAYER_TOPOLOGY, "boundary", "Boundary", "Контур", "A defined edge across which ownership, data or effects must be checked."),
    CONCEPT(REAPER_ARCH_CONCEPT_PERIMETER, REAPER_ARCH_LAYER_TOPOLOGY, "perimeter", "Perimeter", "Периметр", "The complete protected scope of a system, process or execution capability."),
    CONCEPT(REAPER_ARCH_CONCEPT_WORK_ENVIRONMENT, REAPER_ARCH_LAYER_WORKSPACE, "work-environment", "Work environment", "Рабочая среда", "The installed and configured tools needed for a defined development or operation task."),
    CONCEPT(REAPER_ARCH_CONCEPT_WORKSPACE, REAPER_ARCH_LAYER_WORKSPACE, "workspace", "Workspace", "Рабочая область", "A project-scoped area for source, configuration, artifacts and task state."),
    CONCEPT(REAPER_ARCH_CONCEPT_FOOTHOLD, REAPER_ARCH_LAYER_WORKSPACE, "foothold", "Foothold", "Плацдарм", "A stable entry point from which a larger integration or migration can proceed."),
    CONCEPT(REAPER_ARCH_CONCEPT_ANCHOR_POINT, REAPER_ARCH_LAYER_WORKSPACE, "anchor-point", "Anchor point", "Опорная точка", "A named stable reference such as an ABI version, invariant or release boundary."),
    CONCEPT(REAPER_ARCH_CONCEPT_BASELINE, REAPER_ARCH_LAYER_WORKSPACE, "baseline", "Baseline", "Базовая линия", "A measured reference state used to detect regressions and evaluate change."),
    CONCEPT(REAPER_ARCH_CONCEPT_LOAD_BEARING_STRUCTURE, REAPER_ARCH_LAYER_FOUNDATION, "load-bearing-structure", "Load-bearing structure", "Несущая конструкция", "A critical dependency layer whose contracts must remain stable for dependent systems."),
    CONCEPT(REAPER_ARCH_CONCEPT_HARDWARE_SOFTWARE_BASE, REAPER_ARCH_LAYER_HARDWARE_INTEGRATION, "hardware-software-base", "Hardware/software base", "Аппаратно-программная база", "The explicit hardware, firmware, driver and host-ABI boundary; privileged access stays in trusted adapters."),
    CONCEPT(REAPER_ARCH_CONCEPT_SOFTWARE_FRAMEWORK, REAPER_ARCH_LAYER_FOUNDATION, "software-framework", "Software framework", "Программный каркас", "A reusable system of lifecycle rules, extension points and shared services for applications.")
};

#undef CONCEPT

static void set_error(ReaperArchitectureError *error,
                      ReaperArchitectureStatus status,
                      ReaperArchitectureConceptId concept_id,
                      const char *message) {
    if (error == NULL) return;
    error->status = status;
    error->concept_id = concept_id;
    (void)snprintf(error->message, sizeof(error->message), "%s", message);
}

static size_t find_concept_index(const ReaperArchitectureGraph *graph,
                                 ReaperArchitectureConceptId id) {
    size_t index;
    for (index = 0U; index < graph->concept_count; ++index) {
        if (graph->concepts[index] == id) return index;
    }
    return graph->concept_count;
}

static int visit_node(const ReaperArchitectureGraph *graph,
                      size_t node_index,
                      unsigned char state[REAPER_ARCHITECTURE_MAX_CONCEPTS]) {
    size_t edge_index;
    ReaperArchitectureConceptId id = graph->concepts[node_index];

    state[node_index] = 1U;
    for (edge_index = 0U; edge_index < graph->dependency_count; ++edge_index) {
        size_t dependency_index;
        if (graph->dependencies[edge_index].dependent != id) continue;
        dependency_index = find_concept_index(
            graph, graph->dependencies[edge_index].dependency);
        if (state[dependency_index] == 1U) return 0;
        if (state[dependency_index] == 0U &&
            !visit_node(graph, dependency_index, state)) return 0;
    }
    state[node_index] = 2U;
    return 1;
}

size_t reaper_architecture_concept_count(void) {
    return sizeof(CONCEPTS) / sizeof(CONCEPTS[0]);
}

size_t reaper_architecture_layer_count(void) {
    return sizeof(LAYERS) / sizeof(LAYERS[0]);
}

const ReaperArchitectureConceptInfo *reaper_architecture_concept_at(size_t index) {
    return index < reaper_architecture_concept_count() ? &CONCEPTS[index] : NULL;
}

const ReaperArchitectureConceptInfo *reaper_architecture_concept_find_by_id(
    ReaperArchitectureConceptId id
) {
    if ((unsigned int)id == 0U ||
        (unsigned int)id > (unsigned int)reaper_architecture_concept_count()) {
        return NULL;
    }
    return &CONCEPTS[(size_t)((unsigned int)id - 1U)];
}

const ReaperArchitectureConceptInfo *reaper_architecture_concept_find(
    const char *key
) {
    size_t index;
    if (key == NULL || key[0] == '\0') return NULL;
    for (index = 0U; index < reaper_architecture_concept_count(); ++index) {
        if (strcmp(CONCEPTS[index].key, key) == 0) return &CONCEPTS[index];
    }
    return NULL;
}

const ReaperArchitectureConceptInfo *reaper_architecture_concept_find_ru(
    const char *name_ru
) {
    size_t index;
    if (name_ru == NULL || name_ru[0] == '\0') return NULL;
    for (index = 0U; index < reaper_architecture_concept_count(); ++index) {
        if (strcmp(CONCEPTS[index].name_ru, name_ru) == 0) return &CONCEPTS[index];
    }
    return NULL;
}

const ReaperArchitectureLayerInfo *reaper_architecture_layer_at(size_t index) {
    return index < reaper_architecture_layer_count() ? &LAYERS[index] : NULL;
}

ReaperArchitectureStatus reaper_architecture_graph_validate(
    const ReaperArchitectureGraph *graph,
    ReaperArchitectureError *error
) {
    size_t index;
    size_t edge_index;
    unsigned char state[REAPER_ARCHITECTURE_MAX_CONCEPTS] = {0U};

    if (graph == NULL ||
        (graph->concept_count > 0U && graph->concepts == NULL) ||
        (graph->dependency_count > 0U && graph->dependencies == NULL)) {
        set_error(error, REAPER_ARCHITECTURE_INVALID_ARGUMENT,
                  (ReaperArchitectureConceptId)0, "graph or graph storage is null");
        return REAPER_ARCHITECTURE_INVALID_ARGUMENT;
    }
    if (graph->concept_count > REAPER_ARCHITECTURE_MAX_CONCEPTS ||
        graph->dependency_count > REAPER_ARCHITECTURE_MAX_DEPENDENCIES) {
        set_error(error, REAPER_ARCHITECTURE_LIMIT_EXCEEDED,
                  (ReaperArchitectureConceptId)0, "graph exceeds the v1 node or edge limit");
        return REAPER_ARCHITECTURE_LIMIT_EXCEEDED;
    }

    for (index = 0U; index < graph->concept_count; ++index) {
        ReaperArchitectureConceptId id = graph->concepts[index];
        size_t previous;
        if (reaper_architecture_concept_find_by_id(id) == NULL) {
            set_error(error, REAPER_ARCHITECTURE_UNKNOWN_CONCEPT, id,
                      "graph contains an unknown concept id");
            return REAPER_ARCHITECTURE_UNKNOWN_CONCEPT;
        }
        for (previous = 0U; previous < index; ++previous) {
            if (graph->concepts[previous] == id) {
                set_error(error, REAPER_ARCHITECTURE_DUPLICATE_CONCEPT, id,
                          "graph contains a duplicate concept id");
                return REAPER_ARCHITECTURE_DUPLICATE_CONCEPT;
            }
        }
    }

    for (edge_index = 0U; edge_index < graph->dependency_count; ++edge_index) {
        const ReaperArchitectureDependency *edge = &graph->dependencies[edge_index];
        size_t previous;
        if (reaper_architecture_concept_find_by_id(edge->dependent) == NULL ||
            reaper_architecture_concept_find_by_id(edge->dependency) == NULL) {
            set_error(error, REAPER_ARCHITECTURE_UNKNOWN_CONCEPT,
                      edge->dependent, "dependency references an unknown concept id");
            return REAPER_ARCHITECTURE_UNKNOWN_CONCEPT;
        }
        if (find_concept_index(graph, edge->dependent) == graph->concept_count) {
            set_error(error, REAPER_ARCHITECTURE_MISSING_CONCEPT, edge->dependent,
                      "dependent concept is not present in the graph");
            return REAPER_ARCHITECTURE_MISSING_CONCEPT;
        }
        if (find_concept_index(graph, edge->dependency) == graph->concept_count) {
            set_error(error, REAPER_ARCHITECTURE_MISSING_DEPENDENCY, edge->dependency,
                      "dependency concept is not present in the graph");
            return REAPER_ARCHITECTURE_MISSING_DEPENDENCY;
        }
        if (edge->dependent == edge->dependency) {
            set_error(error, REAPER_ARCHITECTURE_SELF_DEPENDENCY, edge->dependent,
                      "a concept cannot depend on itself");
            return REAPER_ARCHITECTURE_SELF_DEPENDENCY;
        }
        for (previous = 0U; previous < edge_index; ++previous) {
            if (graph->dependencies[previous].dependent == edge->dependent &&
                graph->dependencies[previous].dependency == edge->dependency) {
                set_error(error, REAPER_ARCHITECTURE_DUPLICATE_DEPENDENCY,
                          edge->dependent, "graph contains a duplicate dependency edge");
                return REAPER_ARCHITECTURE_DUPLICATE_DEPENDENCY;
            }
        }
    }

    for (index = 0U; index < graph->concept_count; ++index) {
        if (state[index] == 0U && !visit_node(graph, index, state)) {
            set_error(error, REAPER_ARCHITECTURE_DEPENDENCY_CYCLE,
                      graph->concepts[index], "dependency graph contains a cycle");
            return REAPER_ARCHITECTURE_DEPENDENCY_CYCLE;
        }
    }

    set_error(error, REAPER_ARCHITECTURE_OK, (ReaperArchitectureConceptId)0, "ok");
    return REAPER_ARCHITECTURE_OK;
}

ReaperArchitectureStatus reaper_architecture_graph_order(
    const ReaperArchitectureGraph *graph,
    ReaperArchitectureConceptId *ordered,
    size_t capacity,
    size_t *written,
    ReaperArchitectureError *error
) {
    size_t incoming[REAPER_ARCHITECTURE_MAX_CONCEPTS] = {0U};
    unsigned char emitted[REAPER_ARCHITECTURE_MAX_CONCEPTS] = {0U};
    size_t index;
    size_t count = 0U;
    ReaperArchitectureStatus status;

    if (written == NULL) {
        set_error(error, REAPER_ARCHITECTURE_INVALID_ARGUMENT,
                  (ReaperArchitectureConceptId)0, "written is required");
        return REAPER_ARCHITECTURE_INVALID_ARGUMENT;
    }
    *written = 0U;
    status = reaper_architecture_graph_validate(graph, error);
    if (status != REAPER_ARCHITECTURE_OK) return status;
    if (capacity < graph->concept_count) {
        set_error(error, REAPER_ARCHITECTURE_BUFFER_TOO_SMALL,
                  (ReaperArchitectureConceptId)0, "output buffer is smaller than graph node count");
        return REAPER_ARCHITECTURE_BUFFER_TOO_SMALL;
    }
    if (graph->concept_count > 0U && ordered == NULL) {
        set_error(error, REAPER_ARCHITECTURE_INVALID_ARGUMENT,
                  (ReaperArchitectureConceptId)0, "ordered output buffer is null");
        return REAPER_ARCHITECTURE_INVALID_ARGUMENT;
    }

    for (index = 0U; index < graph->dependency_count; ++index) {
        size_t dependent_index = find_concept_index(
            graph, graph->dependencies[index].dependent);
        incoming[dependent_index] += 1U;
    }

    while (count < graph->concept_count) {
        size_t candidate = graph->concept_count;
        size_t candidate_scan;
        ReaperArchitectureConceptId selected_id = (ReaperArchitectureConceptId)0;

        for (candidate_scan = 0U; candidate_scan < graph->concept_count; ++candidate_scan) {
            if (emitted[candidate_scan] != 0U || incoming[candidate_scan] != 0U) continue;
            if (candidate == graph->concept_count ||
                (unsigned int)graph->concepts[candidate_scan] < (unsigned int)selected_id) {
                candidate = candidate_scan;
                selected_id = graph->concepts[candidate_scan];
            }
        }
        if (candidate == graph->concept_count) {
            set_error(error, REAPER_ARCHITECTURE_DEPENDENCY_CYCLE,
                      (ReaperArchitectureConceptId)0, "no dependency-free node remains");
            return REAPER_ARCHITECTURE_DEPENDENCY_CYCLE;
        }

        emitted[candidate] = 1U;
        ordered[count] = graph->concepts[candidate];
        count += 1U;

        for (index = 0U; index < graph->dependency_count; ++index) {
            if (graph->dependencies[index].dependency == graph->concepts[candidate]) {
                size_t dependent_index = find_concept_index(
                    graph, graph->dependencies[index].dependent);
                if (incoming[dependent_index] > 0U) incoming[dependent_index] -= 1U;
            }
        }
    }

    *written = count;
    set_error(error, REAPER_ARCHITECTURE_OK, (ReaperArchitectureConceptId)0, "ok");
    return REAPER_ARCHITECTURE_OK;
}

const char *reaper_architecture_status_name(ReaperArchitectureStatus status) {
    switch (status) {
        case REAPER_ARCHITECTURE_OK: return "ok";
        case REAPER_ARCHITECTURE_INVALID_ARGUMENT: return "invalid-argument";
        case REAPER_ARCHITECTURE_LIMIT_EXCEEDED: return "limit-exceeded";
        case REAPER_ARCHITECTURE_UNKNOWN_CONCEPT: return "unknown-concept";
        case REAPER_ARCHITECTURE_DUPLICATE_CONCEPT: return "duplicate-concept";
        case REAPER_ARCHITECTURE_MISSING_CONCEPT: return "missing-concept";
        case REAPER_ARCHITECTURE_MISSING_DEPENDENCY: return "missing-dependency";
        case REAPER_ARCHITECTURE_SELF_DEPENDENCY: return "self-dependency";
        case REAPER_ARCHITECTURE_DUPLICATE_DEPENDENCY: return "duplicate-dependency";
        case REAPER_ARCHITECTURE_DEPENDENCY_CYCLE: return "dependency-cycle";
        case REAPER_ARCHITECTURE_BUFFER_TOO_SMALL: return "buffer-too-small";
    }
    return "unknown-status";
}
