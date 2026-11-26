#include "reaper/architecture.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_catalog_is_complete_and_stable(void) {
    size_t index;
    assert(reaper_architecture_concept_count() == REAPER_ARCHITECTURE_CONCEPT_COUNT);
    assert(reaper_architecture_layer_count() == (size_t)REAPER_ARCH_LAYER_COUNT);
    for (index = 0U; index < reaper_architecture_concept_count(); ++index) {
        const ReaperArchitectureConceptInfo *info = reaper_architecture_concept_at(index);
        assert(info != NULL);
        assert((unsigned int)info->id == (unsigned int)(index + 1U));
        assert(info->key != NULL && info->key[0] != '\0');
        assert(info->name_en != NULL && info->name_en[0] != '\0');
        assert(info->name_ru != NULL && info->name_ru[0] != '\0');
        assert(info->description != NULL && info->description[0] != '\0');
        assert(reaper_architecture_concept_find_by_id(info->id) == info);
        assert(reaper_architecture_concept_find(info->key) == info);
        assert(reaper_architecture_concept_find_ru(info->name_ru) == info);
    }
    for (index = 0U; index < reaper_architecture_layer_count(); ++index) {
        const ReaperArchitectureLayerInfo *layer = reaper_architecture_layer_at(index);
        assert(layer != NULL);
        assert((size_t)layer->layer == index);
        assert(layer->key != NULL && layer->key[0] != '\0');
        assert(layer->name_en != NULL && layer->name_en[0] != '\0');
        assert(layer->name_ru != NULL && layer->name_ru[0] != '\0');
        assert(layer->description != NULL && layer->description[0] != '\0');
    }
    assert(reaper_architecture_concept_at(66U) == NULL);
    assert(reaper_architecture_concept_find_by_id((ReaperArchitectureConceptId)0) == NULL);
    assert(reaper_architecture_concept_find("missing") == NULL);
    assert(reaper_architecture_concept_find(NULL) == NULL);
    assert(reaper_architecture_concept_find_ru("Каркас ") == NULL);
    assert(reaper_architecture_concept_find_ru("Рабочая среда")->layer == REAPER_ARCH_LAYER_WORKSPACE);
    assert(reaper_architecture_concept_find_ru("Рабочая область")->layer == REAPER_ARCH_LAYER_WORKSPACE);
    assert(reaper_architecture_layer_at(9U) == NULL);
}

static void test_graph_validation_and_deterministic_order(void) {
    const ReaperArchitectureConceptId concepts[] = {
        REAPER_ARCH_CONCEPT_RUNTIME,
        REAPER_ARCH_CONCEPT_HOST,
        REAPER_ARCH_CONCEPT_BASE_LAYER,
        REAPER_ARCH_CONCEPT_PLATFORM
    };
    const ReaperArchitectureDependency dependencies[] = {
        { REAPER_ARCH_CONCEPT_RUNTIME, REAPER_ARCH_CONCEPT_HOST },
        { REAPER_ARCH_CONCEPT_RUNTIME, REAPER_ARCH_CONCEPT_BASE_LAYER },
        { REAPER_ARCH_CONCEPT_HOST, REAPER_ARCH_CONCEPT_PLATFORM }
    };
    const ReaperArchitectureConceptId expected[] = {
        REAPER_ARCH_CONCEPT_PLATFORM,
        REAPER_ARCH_CONCEPT_BASE_LAYER,
        REAPER_ARCH_CONCEPT_HOST,
        REAPER_ARCH_CONCEPT_RUNTIME
    };
    ReaperArchitectureGraph graph = {
        concepts, sizeof(concepts) / sizeof(concepts[0]),
        dependencies, sizeof(dependencies) / sizeof(dependencies[0])
    };
    ReaperArchitectureConceptId ordered[4];
    ReaperArchitectureError error;
    size_t written = 0U;

    assert(reaper_architecture_graph_validate(&graph, &error) == REAPER_ARCHITECTURE_OK);
    assert(error.status == REAPER_ARCHITECTURE_OK);
    assert(strcmp(error.message, "ok") == 0);
    assert(reaper_architecture_graph_order(&graph, ordered, 4U, &written, &error) ==
           REAPER_ARCHITECTURE_OK);
    assert(written == 4U);
    assert(memcmp(ordered, expected, sizeof(expected)) == 0);
    assert(strcmp(reaper_architecture_status_name(REAPER_ARCHITECTURE_OK), "ok") == 0);
}

static void test_empty_graph_is_valid(void) {
    ReaperArchitectureGraph graph = { NULL, 0U, NULL, 0U };
    ReaperArchitectureError error;
    size_t written = 7U;
    assert(reaper_architecture_graph_validate(&graph, &error) == REAPER_ARCHITECTURE_OK);
    assert(reaper_architecture_graph_order(&graph, NULL, 0U, &written, &error) ==
           REAPER_ARCHITECTURE_OK);
    assert(written == 0U);
}

static void test_invalid_graphs_are_rejected(void) {
    ReaperArchitectureError error;
    ReaperArchitectureGraph graph;
    const ReaperArchitectureConceptId unknown[] = {(ReaperArchitectureConceptId)99};
    const ReaperArchitectureConceptId duplicate[] = {
        REAPER_ARCH_CONCEPT_HOST, REAPER_ARCH_CONCEPT_HOST
    };
    const ReaperArchitectureConceptId two[] = {
        REAPER_ARCH_CONCEPT_HOST, REAPER_ARCH_CONCEPT_RUNTIME
    };
    const ReaperArchitectureDependency missing[] = {
        { REAPER_ARCH_CONCEPT_RUNTIME, REAPER_ARCH_CONCEPT_PLATFORM }
    };
    const ReaperArchitectureDependency self[] = {
        { REAPER_ARCH_CONCEPT_HOST, REAPER_ARCH_CONCEPT_HOST }
    };
    const ReaperArchitectureDependency duplicate_edges[] = {
        { REAPER_ARCH_CONCEPT_RUNTIME, REAPER_ARCH_CONCEPT_HOST },
        { REAPER_ARCH_CONCEPT_RUNTIME, REAPER_ARCH_CONCEPT_HOST }
    };
    const ReaperArchitectureDependency cycle[] = {
        { REAPER_ARCH_CONCEPT_HOST, REAPER_ARCH_CONCEPT_RUNTIME },
        { REAPER_ARCH_CONCEPT_RUNTIME, REAPER_ARCH_CONCEPT_HOST }
    };

    graph = (ReaperArchitectureGraph){unknown, 1U, NULL, 0U};
    assert(reaper_architecture_graph_validate(&graph, &error) ==
           REAPER_ARCHITECTURE_UNKNOWN_CONCEPT);

    graph = (ReaperArchitectureGraph){duplicate, 2U, NULL, 0U};
    assert(reaper_architecture_graph_validate(&graph, &error) ==
           REAPER_ARCHITECTURE_DUPLICATE_CONCEPT);

    graph = (ReaperArchitectureGraph){two, 2U, missing, 1U};
    assert(reaper_architecture_graph_validate(&graph, &error) ==
           REAPER_ARCHITECTURE_MISSING_DEPENDENCY);

    graph = (ReaperArchitectureGraph){two, 2U, self, 1U};
    assert(reaper_architecture_graph_validate(&graph, &error) ==
           REAPER_ARCHITECTURE_SELF_DEPENDENCY);

    graph = (ReaperArchitectureGraph){two, 2U, duplicate_edges, 2U};
    assert(reaper_architecture_graph_validate(&graph, &error) ==
           REAPER_ARCHITECTURE_DUPLICATE_DEPENDENCY);

    graph = (ReaperArchitectureGraph){two, 2U, cycle, 2U};
    assert(reaper_architecture_graph_validate(&graph, &error) ==
           REAPER_ARCHITECTURE_DEPENDENCY_CYCLE);
}

static void test_limits_arguments_and_output_capacity(void) {
    ReaperArchitectureError error;
    ReaperArchitectureGraph graph;
    const ReaperArchitectureConceptId one[] = {REAPER_ARCH_CONCEPT_PLATFORM};
    ReaperArchitectureConceptId output[1];
    size_t written = 0U;

    assert(reaper_architecture_graph_validate(NULL, &error) ==
           REAPER_ARCHITECTURE_INVALID_ARGUMENT);
    graph = (ReaperArchitectureGraph){NULL, 1U, NULL, 0U};
    assert(reaper_architecture_graph_validate(&graph, &error) ==
           REAPER_ARCHITECTURE_INVALID_ARGUMENT);
    graph = (ReaperArchitectureGraph){one, 1U, NULL, 0U};
    assert(reaper_architecture_graph_order(&graph, output, 0U, &written, &error) ==
           REAPER_ARCHITECTURE_BUFFER_TOO_SMALL);
    assert(written == 0U);
    assert(reaper_architecture_graph_order(&graph, NULL, 1U, &written, &error) ==
           REAPER_ARCHITECTURE_INVALID_ARGUMENT);
    assert(reaper_architecture_graph_order(&graph, output, 1U, NULL, &error) ==
           REAPER_ARCHITECTURE_INVALID_ARGUMENT);
    assert(reaper_architecture_status_name(REAPER_ARCHITECTURE_DEPENDENCY_CYCLE) != NULL);
}

int main(void) {
    test_catalog_is_complete_and_stable();
    test_graph_validation_and_deterministic_order();
    test_empty_graph_is_valid();
    test_invalid_graphs_are_rejected();
    test_limits_arguments_and_output_capacity();
    puts("reaper architecture registry tests passed");
    return 0;
}
