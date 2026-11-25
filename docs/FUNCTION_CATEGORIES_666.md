# Psychoporter 666 — function categories

**Canonical registry:** [`language/functions_666.json`](../language/functions_666.json)  
**Category scheme:** `dak-reaper-architecture/v1`  
**Registry size:** 666 stable function IDs

This page is the human-readable category view. The JSON registry remains the source of truth for function names, contracts, implementation states, source references and acceptance criteria. The 13 original MOST registry groups are preserved; every entry is additionally assigned to exactly one of the seven architecture categories below.

## Category overview

| Category ID | Category | Functions | Original groups |
|---|---|---:|---|
| `kernel-runtime` | Ядро, память и конкурентное исполнение | 121 | MOST-MEM-BASE, MOST-EXEC |
| `language-compiler` | Язык Reaper, типовая система и компилятор | 260 | MOST-TYPE-BASE, MOST-COMP-BASE, MOST-BRIDGE, MOST-TYPES, MOST-TOOL |
| `desktop-ui` | Рабочий стол, UI и взаимодействие | 22 | MOST-UI-BASE |
| `network-distributed` | Сеть и распределённые системы | 21 | MOST-NET-BASE |
| `storage-data` | Хранение, схемы и данные | 121 | MOST-DATA-BASE, MOST-DATA |
| `security-resilience` | Безопасность, доверие и восстановление | 100 | MOST-SEC |
| `ecosystem-tooling` | Экосистема, интеграции и сопровождение | 21 | MOST-ECOSYS-BASE |

**Total: 666 functions.** No ID is renumbered or reused. Original group boundaries and domain labels remain intact.

## Ядро, память и конкурентное исполнение — 121

`kernel-runtime` · Физическая и виртуальная память, регионы, аллокаторы, управление задачами, потоки, атомики, блокировки, очереди и IPC-примитивы.

### Память, регионы и аппаратный уровень — 1–21

- `MOST-FN-001` — `снимок_региона`
- `MOST-FN-002` — `бюджет_памяти`
- `MOST-FN-003` — `страница_ro`
- `MOST-FN-004` — `стереть_при_освобождении`
- `MOST-FN-005` — `упаковать_по_доступности`
- `MOST-FN-006` — `горячее / холодное`
- `MOST-FN-007` — `предзагрузка_шага`
- `MOST-FN-008` — `кольцо_виртуальное`
- `MOST-FN-009` — `порог_фрагментации`
- `MOST-FN-010` — `сид_размещения`
- `MOST-FN-011` — `банк_памяти`
- `MOST-FN-012` — `dma_канал`
- `MOST-FN-013` — `лимит_кадров`
- `MOST-FN-014` — `атомарно_сравнить_и_обновить`
- `MOST-FN-015` — `домен_безопасности`
- `MOST-FN-016` — `слот_потока`
- `MOST-FN-017` — `размер_кадра_корутины`
- `MOST-FN-018` — `пул_однотипных`
- `MOST-FN-019` — `проверить_выравнивание`
- `MOST-FN-020` — `разделить_по_смещению`
- `MOST-FN-021` — `при_отмене`

### Потоки, конкурентность и память — 311–410

- `MOST-FN-311` — `memory_arena_create`
- `MOST-FN-312` — `memory_arena_allocate`
- `MOST-FN-313` — `memory_arena_allocate_zeroed`
- `MOST-FN-314` — `memory_arena_checkpoint`
- `MOST-FN-315` — `memory_arena_rewind`
- `MOST-FN-316` — `memory_arena_reset`
- `MOST-FN-317` — `memory_arena_destroy`
- `MOST-FN-318` — `memory_arena_stats`
- `MOST-FN-319` — `memory_arena_high_water`
- `MOST-FN-320` — `memory_arena_clear_released`
- `MOST-FN-321` — `memory_region_open`
- `MOST-FN-322` — `memory_region_close`
- `MOST-FN-323` — `memory_region_contains`
- `MOST-FN-324` — `memory_region_promote`
- `MOST-FN-325` — `memory_region_escape_check`
- `MOST-FN-326` — `memory_region_snapshot`
- `MOST-FN-327` — `memory_region_rollback`
- `MOST-FN-328` — `memory_region_commit`
- `MOST-FN-329` — `memory_borrow_shared`
- `MOST-FN-330` — `memory_borrow_mutable`
- `MOST-FN-331` — `memory_borrow_end`
- `MOST-FN-332` — `memory_move_value`
- `MOST-FN-333` — `memory_move_check`
- `MOST-FN-334` — `memory_drop_register`
- `MOST-FN-335` — `memory_drop_run`
- `MOST-FN-336` — `memory_linear_consume`
- `MOST-FN-337` — `memory_linear_transfer`
- `MOST-FN-338` — `memory_handle_validate`
- `MOST-FN-339` — `memory_slice_create`
- `MOST-FN-340` — `memory_slice_split`
- `MOST-FN-341` — `memory_slice_join`
- `MOST-FN-342` — `memory_slice_get`
- `MOST-FN-343` — `memory_slice_set`
- `MOST-FN-344` — `memory_slice_subslice`
- `MOST-FN-345` — `memory_slice_bounds_check`
- `MOST-FN-346` — `memory_aligned_allocate`
- `MOST-FN-347` — `memory_alignment_check`
- `MOST-FN-348` — `memory_typed_view_create`
- `MOST-FN-349` — `memory_typed_view_validate`
- `MOST-FN-350` — `memory_typed_view_read`
- `MOST-FN-351` — `memory_typed_view_write`
- `MOST-FN-352` — `memory_pool_create`
- `MOST-FN-353` — `memory_pool_allocate`
- `MOST-FN-354` — `memory_pool_free`
- `MOST-FN-355` — `memory_pool_reset`
- `MOST-FN-356` — `memory_allocator_select`
- `MOST-FN-357` — `memory_allocator_stats`
- `MOST-FN-358` — `memory_stack_budget_check`
- `MOST-FN-359` — `memory_heap_budget_check`
- `MOST-FN-360` — `memory_dma_buffer_validate`
- `MOST-FN-361` — `task_scope_open`
- `MOST-FN-362` — `task_spawn`
- `MOST-FN-363` — `task_join`
- `MOST-FN-364` — `task_cancel`
- `MOST-FN-365` — `task_cancelled`
- `MOST-FN-366` — `task_budget_set`
- `MOST-FN-367` — `task_deadline_set`
- `MOST-FN-368` — `task_result_read`
- `MOST-FN-369` — `task_group_create`
- `MOST-FN-370` — `task_group_wait`
- `MOST-FN-371` — `scheduler_enqueue`
- `MOST-FN-372` — `scheduler_dequeue`
- `MOST-FN-373` — `scheduler_step`
- `MOST-FN-374` — `scheduler_drain`
- `MOST-FN-375` — `actor_create`
- `MOST-FN-376` — `actor_send`
- `MOST-FN-377` — `actor_receive`
- `MOST-FN-378` — `actor_stop`
- `MOST-FN-379` — `actor_restart`
- `MOST-FN-380` — `channel_create`
- `MOST-FN-381` — `channel_send`
- `MOST-FN-382` — `channel_receive`
- `MOST-FN-383` — `channel_close`
- `MOST-FN-384` — `channel_capacity`
- `MOST-FN-385` — `channel_backpressure`
- `MOST-FN-386` — `channel_select`
- `MOST-FN-387` — `channel_timeout`
- `MOST-FN-388` — `channel_try_send`
- `MOST-FN-389` — `channel_try_receive`
- `MOST-FN-390` — `mailbox_create`
- `MOST-FN-391` — `mailbox_publish`
- `MOST-FN-392` — `mailbox_read`
- `MOST-FN-393` — `atomic_load`
- `MOST-FN-394` — `atomic_store`
- `MOST-FN-395` — `atomic_exchange`
- `MOST-FN-396` — `atomic_compare_exchange`
- `MOST-FN-397` — `atomic_fetch_add`
- `MOST-FN-398` — `atomic_fence`
- `MOST-FN-399` — `memory_order_validate`
- `MOST-FN-400` — `mutex_create`
- `MOST-FN-401` — `mutex_lock`
- `MOST-FN-402` — `mutex_try_lock`
- `MOST-FN-403` — `mutex_unlock`
- `MOST-FN-404` — `rwlock_read`
- `MOST-FN-405` — `rwlock_write`
- `MOST-FN-406` — `semaphore_acquire`
- `MOST-FN-407` — `semaphore_release`
- `MOST-FN-408` — `wait_group_create`
- `MOST-FN-409` — `wait_group_add`
- `MOST-FN-410` — `wait_group_wait`

## Язык Reaper, типовая система и компилятор — 260

`language-compiler` · Семантика и типы языка, MOST frontend, компиляция и анализ, IR, контракты, математика, диагностические и toolchain API.

### Типы, контракты и выразительность — 22–41

- `MOST-FN-022` — `уточнить_тип`
- `MOST-FN-023` — `опционал_с_причиной`
- `MOST-FN-024` — `одно_из`
- `MOST-FN-025` — `массив[N]`
- `MOST-FN-026` — `перечисление_с_правилом`
- `MOST-FN-027` — `именованный_кортеж`
- `MOST-FN-028` — `единицы_измерения`
- `MOST-FN-029` — `режим_округления`
- `MOST-FN-030` — `насыщающий_и_модульный_тип`
- `MOST-FN-031` — `инвариант`
- `MOST-FN-032` — `было(...)`
- `MOST-FN-033` — `расширить`
- `MOST-FN-034` — `ошибка_набора`
- `MOST-FN-035` — `фаза<T>`
- `MOST-FN-036` — `чистая`
- `MOST-FN-037` — `без_аллокаций`
- `MOST-FN-038` — `ограничение_цикла`
- `MOST-FN-039` — `новый_тип`
- `MOST-FN-040` — `маска<T>`
- `MOST-FN-041` — `локальный_тип`

### Компилятор, метапрограммирование и анализ — 85–105

- `MOST-FN-085` — `отражение_типа`
- `MOST-FN-086` — `дерево_синтаксиса`
- `MOST-FN-087` — `ошибка_компиляции / предупреждение_компиляции`
- `MOST-FN-088` — `оценка_сложности`
- `MOST-FN-089` — `детектор_мертвого_кода`
- `MOST-FN-090` — `лимит_сложности`
- `MOST-FN-091` — `граф_зависимостей`
- `MOST-FN-092` — `мок_контракта`
- `MOST-FN-093` — `свойство_тест`
- `MOST-FN-094` — `снимок_вывода`
- `MOST-FN-095` — `бюджет_теста`
- `MOST-FN-096` — `матрица_сборки`
- `MOST-FN-097` — `причина_и_исправление`
- `MOST-FN-098` — `перемешать_с_сидом`
- `MOST-FN-099` — `неблокирующий_путь`
- `MOST-FN-100` — `утверждение_доказуемое`
- `MOST-FN-101` — `схема_типа`
- `MOST-FN-102` — `профиль_строк`
- `MOST-FN-103` — `визуализация_памяти`
- `MOST-FN-104` — `не_ноль<T>`
- `MOST-FN-105` — `сухой_прогон`

### Двухслойный синтаксис REAPER ↔ MOST — 148–220

- `MOST-FN-148` — `most_lexer_normalize_identifier`
- `MOST-FN-149` — `most_lexer_segment_identifier`
- `MOST-FN-150` — `most_lexer_fold_unicode`
- `MOST-FN-151` — `most_lexer_validate_codepoint`
- `MOST-FN-152` — `most_lexer_escape_identifier`
- `MOST-FN-153` — `most_lexer_tokenize_word`
- `MOST-FN-154` — `most_lexer_preserve_span`
- `MOST-FN-155` — `most_lexer_classify_script`
- `MOST-FN-156` — `most_lexer_decode_escape`
- `MOST-FN-157` — `most_lexer_normalize_operator`
- `MOST-FN-158` — `most_lexer_validate_utf8`
- `MOST-FN-159` — `most_morphology_inflect_noun`
- `MOST-FN-160` — `most_morphology_inflect_verb`
- `MOST-FN-161` — `most_morphology_stem_word`
- `MOST-FN-162` — `most_morphology_lemma_word`
- `MOST-FN-163` — `most_morphology_tokenize_morpheme`
- `MOST-FN-164` — `most_morphology_detect_case`
- `MOST-FN-165` — `most_morphology_detect_number`
- `MOST-FN-166` — `most_morphology_detect_gender`
- `MOST-FN-167` — `most_morphology_detect_aspect`
- `MOST-FN-168` — `most_morphology_normalize_diacritic`
- `MOST-FN-169` — `most_dictionary_resolve_synonym`
- `MOST-FN-170` — `most_dictionary_lookup_term`
- `MOST-FN-171` — `most_dictionary_scope_domain`
- `MOST-FN-172` — `most_dictionary_shadow_term`
- `MOST-FN-173` — `most_dictionary_register_alias`
- `MOST-FN-174` — `most_dictionary_deprecate_alias`
- `MOST-FN-175` — `most_dictionary_rank_exact_match`
- `MOST-FN-176` — `most_dictionary_reject_ambiguous`
- `MOST-FN-177` — `most_dictionary_explain_candidate`
- `MOST-FN-178` — `most_dictionary_merge_dictionary`
- `MOST-FN-179` — `most_intent_build_ast`
- `MOST-FN-180` — `most_intent_bind_symbol`
- `MOST-FN-181` — `most_intent_resolve_argument`
- `MOST-FN-182` — `most_intent_resolve_overload`
- `MOST-FN-183` — `most_intent_bind_generic`
- `MOST-FN-184` — `most_intent_infer_context`
- `MOST-FN-185` — `most_intent_validate`
- `MOST-FN-186` — `most_intent_lower_declaration`
- `MOST-FN-187` — `most_intent_lower_expression`
- `MOST-FN-188` — `most_intent_emit_source_map`
- `MOST-FN-189` — `most_source_attach_origin`
- `MOST-FN-190` — `most_source_translate_range`
- `MOST-FN-191` — `most_source_compose_ranges`
- `MOST-FN-192` — `most_source_recover_snippet`
- `MOST-FN-193` — `most_source_preserve_trivia`
- `MOST-FN-194` — `most_source_map_generated_node`
- `MOST-FN-195` — `most_source_map_ir_node`
- `MOST-FN-196` — `most_source_map_diagnostic`
- `MOST-FN-197` — `most_source_compare_frontends`
- `MOST-FN-198` — `most_source_verify_equivalence`
- `MOST-FN-199` — `most_diagnostic_explain_ambiguity`
- `MOST-FN-200` — `most_diagnostic_explain_binding`
- `MOST-FN-201` — `most_diagnostic_explain_type`
- `MOST-FN-202` — `most_diagnostic_explain_effect`
- `MOST-FN-203` — `most_diagnostic_suggest_correction`
- `MOST-FN-204` — `most_diagnostic_rank_suggestions`
- `MOST-FN-205` — `most_diagnostic_format_bilingual`
- `MOST-FN-206` — `most_diagnostic_localize_error`
- `MOST-FN-207` — `most_diagnostic_trace_resolution`
- `MOST-FN-208` — `most_diagnostic_audit_resolution`
- `MOST-FN-209` — `most_interop_parse_mixed_module`
- `MOST-FN-210` — `most_interop_validate_mixed_block`
- `MOST-FN-211` — `most_interop_switch_frontend`
- `MOST-FN-212` — `most_interop_import_reaper_ast`
- `MOST-FN-213` — `most_interop_export_most_ast`
- `MOST-FN-214` — `most_interop_canonicalize_name`
- `MOST-FN-215` — `most_interop_verify_frontend_identity`
- `MOST-FN-216` — `most_interop_serialize_intent`
- `MOST-FN-217` — `most_interop_deserialize_intent`
- `MOST-FN-218` — `most_interop_diff_intent_ast`
- `MOST-FN-219` — `most_interop_generate_glossary`
- `MOST-FN-220` — `most_interop_validate_glossary`

### Типы, контракты и математика — 221–310

- `MOST-FN-221` — `type_define_alias`
- `MOST-FN-222` — `type_define_newtype`
- `MOST-FN-223` — `type_refine_range`
- `MOST-FN-224` — `type_validate_refinement`
- `MOST-FN-225` — `type_option_wrap`
- `MOST-FN-226` — `type_option_unwrap`
- `MOST-FN-227` — `type_result_ok`
- `MOST-FN-228` — `type_result_err`
- `MOST-FN-229` — `type_union_construct`
- `MOST-FN-230` — `type_union_match`
- `MOST-FN-231` — `type_tuple_named`
- `MOST-FN-232` — `type_array_shape`
- `MOST-FN-233` — `type_const_generic`
- `MOST-FN-234` — `type_unit_dimension`
- `MOST-FN-235` — `type_convert_lossless`
- `MOST-FN-236` — `type_convert_checked`
- `MOST-FN-237` — `type_round_checked`
- `MOST-FN-238` — `type_arithmetic_wrapping`
- `MOST-FN-239` — `type_arithmetic_saturating`
- `MOST-FN-240` — `type_arithmetic_checked`
- `MOST-FN-241` — `type_layout_query`
- `MOST-FN-242` — `type_layout_verify`
- `MOST-FN-243` — `type_repr_c`
- `MOST-FN-244` — `type_abi_classify`
- `MOST-FN-245` — `type_callable_signature`
- `MOST-FN-246` — `type_generic_instantiate`
- `MOST-FN-247` — `type_trait_resolve`
- `MOST-FN-248` — `type_exhaustiveness_check`
- `MOST-FN-249` — `type_typestate_transition`
- `MOST-FN-250` — `type_nominal_cast`
- `MOST-FN-251` — `contract_require`
- `MOST-FN-252` — `contract_ensure`
- `MOST-FN-253` — `contract_invariant_check`
- `MOST-FN-254` — `contract_snapshot_old`
- `MOST-FN-255` — `contract_assert`
- `MOST-FN-256` — `contract_prove_range`
- `MOST-FN-257` — `contract_prove_nonzero`
- `MOST-FN-258` — `contract_prove_bounds`
- `MOST-FN-259` — `contract_prove_alignment`
- `MOST-FN-260` — `contract_prove_exhaustive`
- `MOST-FN-261` — `contract_prove_termination_budget`
- `MOST-FN-262` — `contract_effect_row_validate`
- `MOST-FN-263` — `contract_pure_validate`
- `MOST-FN-264` — `contract_noalloc_validate`
- `MOST-FN-265` — `contract_precondition_merge`
- `MOST-FN-266` — `contract_postcondition_merge`
- `MOST-FN-267` — `contract_refinement_compose`
- `MOST-FN-268` — `contract_error_set_collect`
- `MOST-FN-269` — `contract_error_set_check`
- `MOST-FN-270` — `contract_capability_bound`
- `MOST-FN-271` — `contract_lifetime_bound`
- `MOST-FN-272` — `contract_ownership_transfer`
- `MOST-FN-273` — `contract_linear_consumption`
- `MOST-FN-274` — `contract_drop_path_verify`
- `MOST-FN-275` — `contract_layout_stability`
- `MOST-FN-276` — `contract_abi_compatibility`
- `MOST-FN-277` — `contract_version_compatibility`
- `MOST-FN-278` — `contract_constant_evaluate`
- `MOST-FN-279` — `contract_unit_consistency`
- `MOST-FN-280` — `contract_generate_report`
- `MOST-FN-281` — `math_checked_add`
- `MOST-FN-282` — `math_checked_subtract`
- `MOST-FN-283` — `math_checked_multiply`
- `MOST-FN-284` — `math_checked_divide`
- `MOST-FN-285` — `math_checked_remainder`
- `MOST-FN-286` — `math_saturating_add`
- `MOST-FN-287` — `math_saturating_subtract`
- `MOST-FN-288` — `math_saturating_multiply`
- `MOST-FN-289` — `math_wrapping_add`
- `MOST-FN-290` — `math_wrapping_subtract`
- `MOST-FN-291` — `math_wrapping_multiply`
- `MOST-FN-292` — `math_gcd`
- `MOST-FN-293` — `math_lcm`
- `MOST-FN-294` — `math_integer_power`
- `MOST-FN-295` — `math_integer_sqrt`
- `MOST-FN-296` — `math_hypot`
- `MOST-FN-297` — `math_fused_multiply_add`
- `MOST-FN-298` — `math_clamp`
- `MOST-FN-299` — `math_lerp`
- `MOST-FN-300` — `math_map_range`
- `MOST-FN-301` — `math_dot`
- `MOST-FN-302` — `math_norm`
- `MOST-FN-303` — `math_normalize`
- `MOST-FN-304` — `math_distance`
- `MOST-FN-305` — `math_project`
- `MOST-FN-306` — `math_orthogonal_component`
- `MOST-FN-307` — `math_quadratic_form`
- `MOST-FN-308` — `math_covariance`
- `MOST-FN-309` — `math_variance`
- `MOST-FN-310` — `math_dimension_check`

### Разработка, тестирование и производительность — 611–666

- `MOST-FN-611` — `build_target_resolve`
- `MOST-FN-612` — `build_profile_validate`
- `MOST-FN-613` — `build_dependency_graph`
- `MOST-FN-614` — `build_dependency_lock`
- `MOST-FN-615` — `build_package_manifest`
- `MOST-FN-616` — `build_package_verify`
- `MOST-FN-617` — `build_reproducibility_check`
- `MOST-FN-618` — `build_artifact_hash`
- `MOST-FN-619` — `build_cross_compile_plan`
- `MOST-FN-620` — `build_linker_map_analyze`
- `MOST-FN-621` — `test_case_register`
- `MOST-FN-622` — `test_fixture_load`
- `MOST-FN-623` — `test_property_generate`
- `MOST-FN-624` — `test_property_shrink`
- `MOST-FN-625` — `test_fuzz_corpus_load`
- `MOST-FN-626` — `test_fuzz_mutate`
- `MOST-FN-627` — `test_differential_compare`
- `MOST-FN-628` — `test_golden_snapshot`
- `MOST-FN-629` — `test_contract_execute`
- `MOST-FN-630` — `test_coverage_report`
- `MOST-FN-631` — `test_regression_minimize`
- `MOST-FN-632` — `test_conformance_gate`
- `MOST-FN-633` — `diagnostic_source_excerpt`
- `MOST-FN-634` — `diagnostic_fixit_emit`
- `MOST-FN-635` — `diagnostic_json_encode`
- `MOST-FN-636` — `diagnostic_bilingual_render`
- `MOST-FN-637` — `profile_phase_measure`
- `MOST-FN-638` — `profile_call_graph`
- `MOST-FN-639` — `profile_memory_account`
- `MOST-FN-640` — `profile_hot_path_rank`
- `MOST-FN-641` — `trace_event_emit`
- `MOST-FN-642` — `trace_event_filter`
- `MOST-FN-643` — `trace_session_export`
- `MOST-FN-644` — `resource_leak_report`
- `MOST-FN-645` — `compiler_ast_validate`
- `MOST-FN-646` — `compiler_symbol_table_dump`
- `MOST-FN-647` — `compiler_ir_dump`
- `MOST-FN-648` — `compiler_ir_verify`
- `MOST-FN-649` — `compiler_optimizer_run`
- `MOST-FN-650` — `compiler_optimizer_explain`
- `MOST-FN-651` — `compiler_target_lower`
- `MOST-FN-652` — `compiler_object_emit`
- `MOST-FN-653` — `compiler_wasm_emit`
- `MOST-FN-654` — `compiler_backend_capability_check`
- `MOST-FN-655` — `compiler_cache_key_build`
- `MOST-FN-656` — `compiler_incremental_invalidate`
- `MOST-FN-657` — `format_source_canonical`
- `MOST-FN-658` — `format_source_check`
- `MOST-FN-659` — `lint_source`
- `MOST-FN-660` — `lint_registry`
- `MOST-FN-661` — `doc_example_execute`
- `MOST-FN-662` — `doc_api_index_generate`
- `MOST-FN-663` — `language_server_initialize`
- `MOST-FN-664` — `language_server_complete`
- `MOST-FN-665` — `language_server_hover`
- `MOST-FN-666` — `language_server_rename`

## Рабочий стол, UI и взаимодействие — 22

`desktop-ui` · Компоненты UI, сигналы, рендеринг, состояние интерфейса, доступность, жесты, offline UI и интерактивность.

### Веб, UI и WASM — 42–63

- `MOST-FN-042` — `узел_dom`
- `MOST-FN-043` — `вычислить_сигнал`
- `MOST-FN-044` — `пакет_сигналов`
- `MOST-FN-045` — `список_по_ключу`
- `MOST-FN-046` — `кадр_рендера`
- `MOST-FN-047` — `форма_модель`
- `MOST-FN-048` — `модуль_по_требованию`
- `MOST-FN-049` — `оживить_при_видимости`
- `MOST-FN-050` — `состояние_в_url`
- `MOST-FN-051` — `хранилище_браузера`
- `MOST-FN-052` — `поток_в_ui`
- `MOST-FN-053` — `пружина`
- `MOST-FN-054` — `роль_доступности`
- `MOST-FN-055` — `экран_ширина`
- `MOST-FN-056` — `песочница_компонента`
- `MOST-FN-057` — `аудио_буфер_мост`
- `MOST-FN-058` — `очередь_офлайн`
- `MOST-FN-059` — `метрики_интерфейса`
- `MOST-FN-060` — `маршрут`
- `MOST-FN-061` — `жест`
- `MOST-FN-062` — `сжать_кадр`
- `MOST-FN-063` — `горячая_замена_модуля`

## Сеть и распределённые системы — 21

`network-distributed` · Сетевые кадры и сокеты, ограниченные потоки, таймауты, идемпотентность, трассировка, backpressure и распределённые сообщения.

### Сеть и распределённые системы — 64–84

- `MOST-FN-064` — `протокол_кадр`
- `MOST-FN-065` — `лимит_глубины_и_длины`
- `MOST-FN-066` — `нуль_копий_сеть`
- `MOST-FN-067` — `с_таймаутом`
- `MOST-FN-068` — `повтор_с_откатом`
- `MOST-FN-069` — `прерыватель`
- `MOST-FN-070` — `совместимость_схемы`
- `MOST-FN-071` — `контекст_трассировки`
- `MOST-FN-072` — `пул_соединений`
- `MOST-FN-073` — `ограничитель_частоты`
- `MOST-FN-074` — `ключ_идемпотентности`
- `MOST-FN-075` — `поток_чанков`
- `MOST-FN-076` — `сокет`
- `MOST-FN-077` — `контрольная_сумма<T>`
- `MOST-FN-078` — `возможности`
- `MOST-FN-079` — `логическое_время`
- `MOST-FN-080` — `симуляция_сети`
- `MOST-FN-081` — `прочитать_безопасно`
- `MOST-FN-082` — `канал_сообщений`
- `MOST-FN-083` — `диспетчер_сообщений`
- `MOST-FN-084` — `таймаут_медленного_чтения`

## Хранение, схемы и данные — 121

`storage-data` · Файловые пути и потоки, схемы и миграции, форматы сериализации, кодеки, текст, таблицы, индексы и потоковая обработка данных.

### Данные, текст и бинарные форматы — 106–126

- `MOST-FN-106` — `таблица_колонок`
- `MOST-FN-107` — `битовый_набор`
- `MOST-FN-108` — `малый_вектор / малая_строка`
- `MOST-FN-109` — `поток_значений`
- `MOST-FN-110` — `парсер_среза`
- `MOST-FN-111` — `разобрать_число`
- `MOST-FN-112` — `путь_фс / путь_веб`
- `MOST-FN-113` — `потоковый_разбор`
- `MOST-FN-114` — `префиксное_дерево`
- `MOST-FN-115` — `монотонный_тик / календарь_мгновение`
- `MOST-FN-116` — `ид_уникальный`
- `MOST-FN-117` — `сжать_поток / разжать_поток`
- `MOST-FN-118` — `формат_строки`
- `MOST-FN-119` — `матрица / тензор`
- `MOST-FN-120` — `квантовать / расквантовать`
- `MOST-FN-121` — `журнал_кольцо`
- `MOST-FN-122` — `словарь<K,V>`
- `MOST-FN-123` — `сортировать_устойчиво`
- `MOST-FN-124` — `найти_границу`
- `MOST-FN-125` — `канонизировать`
- `MOST-FN-126` — `регулярное_выражение`

### Данные, схемы, текст и бинарные форматы — 411–510

- `MOST-FN-411` — `schema_define`
- `MOST-FN-412` — `schema_validate`
- `MOST-FN-413` — `schema_evolve`
- `MOST-FN-414` — `schema_diff`
- `MOST-FN-415` — `schema_migrate`
- `MOST-FN-416` — `schema_compatibility_check`
- `MOST-FN-417` — `schema_version_read`
- `MOST-FN-418` — `schema_version_write`
- `MOST-FN-419` — `schema_field_add`
- `MOST-FN-420` — `schema_field_remove`
- `MOST-FN-421` — `schema_enum_validate`
- `MOST-FN-422` — `schema_defaults_apply`
- `MOST-FN-423` — `schema_constraints_check`
- `MOST-FN-424` — `schema_reference_resolve`
- `MOST-FN-425` — `schema_document_generate`
- `MOST-FN-426` — `json_parse_strict`
- `MOST-FN-427` — `json_encode_canonical`
- `MOST-FN-428` — `json_stream_read`
- `MOST-FN-429` — `json_stream_write`
- `MOST-FN-430` — `json_pointer_get`
- `MOST-FN-431` — `json_pointer_set`
- `MOST-FN-432` — `json_patch_apply`
- `MOST-FN-433` — `json_duplicate_key_reject`
- `MOST-FN-434` — `json_resource_limits_check`
- `MOST-FN-435` — `json_schema_validate`
- `MOST-FN-436` — `cbor_parse_bounded`
- `MOST-FN-437` — `cbor_encode_canonical`
- `MOST-FN-438` — `toml_parse_strict`
- `MOST-FN-439` — `toml_encode_canonical`
- `MOST-FN-440` — `csv_parse_records`
- `MOST-FN-441` — `csv_encode_records`
- `MOST-FN-442` — `xml_parse_safe`
- `MOST-FN-443` — `xml_encode_safe`
- `MOST-FN-444` — `yaml_parse_restricted`
- `MOST-FN-445` — `yaml_encode_canonical`
- `MOST-FN-446` — `codec_decode_checked`
- `MOST-FN-447` — `codec_encode_checked`
- `MOST-FN-448` — `codec_version_negotiate`
- `MOST-FN-449` — `codec_unknown_field_policy`
- `MOST-FN-450` — `codec_endian_read`
- `MOST-FN-451` — `codec_endian_write`
- `MOST-FN-452` — `codec_integer_varint_read`
- `MOST-FN-453` — `codec_integer_varint_write`
- `MOST-FN-454` — `codec_checksum_verify`
- `MOST-FN-455` — `codec_frame_length_validate`
- `MOST-FN-456` — `codec_frame_stream_decode`
- `MOST-FN-457` — `codec_frame_stream_encode`
- `MOST-FN-458` — `codec_compression_bounded`
- `MOST-FN-459` — `codec_decompression_bounded`
- `MOST-FN-460` — `codec_roundtrip_verify`
- `MOST-FN-461` — `text_utf8_validate`
- `MOST-FN-462` — `text_utf8_normalize`
- `MOST-FN-463` — `text_grapheme_iterate`
- `MOST-FN-464` — `text_codepoint_iterate`
- `MOST-FN-465` — `text_casefold`
- `MOST-FN-466` — `text_trim_unicode`
- `MOST-FN-467` — `text_split_bounded`
- `MOST-FN-468` — `text_join_bounded`
- `MOST-FN-469` — `text_replace_bounded`
- `MOST-FN-470` — `text_find_all`
- `MOST-FN-471` — `text_regex_compile`
- `MOST-FN-472` — `text_regex_match_bounded`
- `MOST-FN-473` — `text_template_render`
- `MOST-FN-474` — `text_escape_html`
- `MOST-FN-475` — `text_escape_json`
- `MOST-FN-476` — `data_table_create`
- `MOST-FN-477` — `data_table_validate`
- `MOST-FN-478` — `data_column_select`
- `MOST-FN-479` — `data_column_project`
- `MOST-FN-480` — `data_row_filter`
- `MOST-FN-481` — `data_group_by`
- `MOST-FN-482` — `data_aggregate`
- `MOST-FN-483` — `data_join`
- `MOST-FN-484` — `data_sort_stable`
- `MOST-FN-485` — `data_deduplicate`
- `MOST-FN-486` — `data_index_build`
- `MOST-FN-487` — `data_index_lookup`
- `MOST-FN-488` — `data_page_read`
- `MOST-FN-489` — `data_page_write`
- `MOST-FN-490` — `data_cursor_next`
- `MOST-FN-491` — `stream_open`
- `MOST-FN-492` — `stream_read_chunk`
- `MOST-FN-493` — `stream_write_chunk`
- `MOST-FN-494` — `stream_peek`
- `MOST-FN-495` — `stream_skip`
- `MOST-FN-496` — `stream_rewind`
- `MOST-FN-497` — `stream_mark`
- `MOST-FN-498` — `stream_commit_mark`
- `MOST-FN-499` — `stream_backpressure_check`
- `MOST-FN-500` — `stream_rate_limit`
- `MOST-FN-501` — `stream_checksum_fold`
- `MOST-FN-502` — `stream_fan_out`
- `MOST-FN-503` — `stream_merge_ordered`
- `MOST-FN-504` — `stream_tee_bounded`
- `MOST-FN-505` — `stream_close`
- `MOST-FN-506` — `stream_transform`
- `MOST-FN-507` — `stream_filter`
- `MOST-FN-508` — `stream_map`
- `MOST-FN-509` — `stream_concat`
- `MOST-FN-510` — `stream_split`

## Безопасность, доверие и восстановление — 100

`security-resilience` · Capabilities, политики доступа, аудит, криптография, валидация границ, лимиты ресурсов, отказоустойчивость и восстановление.

### Безопасность, политика и устойчивость — 511–610

- `MOST-FN-511` — `capability_define`
- `MOST-FN-512` — `capability_grant`
- `MOST-FN-513` — `capability_revoke`
- `MOST-FN-514` — `capability_require`
- `MOST-FN-515` — `capability_intersect`
- `MOST-FN-516` — `capability_attenuate`
- `MOST-FN-517` — `capability_scope_enter`
- `MOST-FN-518` — `capability_scope_exit`
- `MOST-FN-519` — `capability_check_path`
- `MOST-FN-520` — `capability_check_network`
- `MOST-FN-521` — `capability_check_process`
- `MOST-FN-522` — `capability_check_hardware`
- `MOST-FN-523` — `capability_check_clock`
- `MOST-FN-524` — `capability_check_random`
- `MOST-FN-525` — `capability_check_environment`
- `MOST-FN-526` — `capability_manifest_load`
- `MOST-FN-527` — `capability_manifest_validate`
- `MOST-FN-528` — `capability_policy_evaluate`
- `MOST-FN-529` — `capability_policy_explain`
- `MOST-FN-530` — `capability_denied_report`
- `MOST-FN-531` — `audit_event_append`
- `MOST-FN-532` — `audit_chain_verify`
- `MOST-FN-533` — `audit_checkpoint_create`
- `MOST-FN-534` — `audit_checkpoint_verify`
- `MOST-FN-535` — `audit_log_rotate`
- `MOST-FN-536` — `audit_log_export`
- `MOST-FN-537` — `audit_sensitive_redact`
- `MOST-FN-538` — `audit_actor_bind`
- `MOST-FN-539` — `audit_context_bind`
- `MOST-FN-540` — `audit_policy_change_record`
- `MOST-FN-541` — `audit_ffi_load_record`
- `MOST-FN-542` — `audit_resource_record`
- `MOST-FN-543` — `audit_failure_record`
- `MOST-FN-544` — `audit_integrity_report`
- `MOST-FN-545` — `audit_retention_check`
- `MOST-FN-546` — `audit_signature_verify`
- `MOST-FN-547` — `audit_trust_anchor_load`
- `MOST-FN-548` — `audit_provenance_verify`
- `MOST-FN-549` — `audit_attestation_verify`
- `MOST-FN-550` — `audit_evidence_bundle`
- `MOST-FN-551` — `crypto_hash_sha256`
- `MOST-FN-552` — `crypto_hash_blake2`
- `MOST-FN-553` — `crypto_hmac_compute`
- `MOST-FN-554` — `crypto_hmac_verify`
- `MOST-FN-555` — `crypto_constant_time_equal`
- `MOST-FN-556` — `crypto_random_bytes`
- `MOST-FN-557` — `crypto_nonce_generate`
- `MOST-FN-558` — `crypto_key_id_validate`
- `MOST-FN-559` — `crypto_key_provider_bind`
- `MOST-FN-560` — `crypto_signature_verify`
- `MOST-FN-561` — `crypto_signature_request`
- `MOST-FN-562` — `crypto_kdf_derive`
- `MOST-FN-563` — `crypto_zeroize_buffer`
- `MOST-FN-564` — `crypto_digest_stream`
- `MOST-FN-565` — `crypto_merkle_root`
- `MOST-FN-566` — `crypto_merkle_proof_verify`
- `MOST-FN-567` — `crypto_certificate_parse`
- `MOST-FN-568` — `crypto_certificate_chain_verify`
- `MOST-FN-569` — `crypto_algorithm_policy_check`
- `MOST-FN-570` — `crypto_vector_self_test`
- `MOST-FN-571` — `boundary_path_canonicalize`
- `MOST-FN-572` — `boundary_path_contain`
- `MOST-FN-573` — `boundary_symlink_reject`
- `MOST-FN-574` — `boundary_archive_path_validate`
- `MOST-FN-575` — `boundary_archive_limits_check`
- `MOST-FN-576` — `boundary_file_type_check`
- `MOST-FN-577` — `boundary_file_size_check`
- `MOST-FN-578` — `boundary_native_library_allow`
- `MOST-FN-579` — `boundary_native_abi_check`
- `MOST-FN-580` — `boundary_ffi_symbol_allow`
- `MOST-FN-581` — `boundary_secret_store`
- `MOST-FN-582` — `boundary_secret_reveal`
- `MOST-FN-583` — `boundary_secret_redact`
- `MOST-FN-584` — `boundary_input_validate`
- `MOST-FN-585` — `boundary_output_validate`
- `MOST-FN-586` — `boundary_privilege_drop_plan`
- `MOST-FN-587` — `boundary_process_isolate_request`
- `MOST-FN-588` — `boundary_network_origin_check`
- `MOST-FN-589` — `boundary_resource_quota_check`
- `MOST-FN-590` — `boundary_unsafe_scope_audit`
- `MOST-FN-591` — `resilience_deadline_check`
- `MOST-FN-592` — `resilience_timeout_result`
- `MOST-FN-593` — `resilience_retry_policy_validate`
- `MOST-FN-594` — `resilience_idempotency_check`
- `MOST-FN-595` — `resilience_backoff_compute`
- `MOST-FN-596` — `resilience_jitter_compute`
- `MOST-FN-597` — `resilience_circuit_open`
- `MOST-FN-598` — `resilience_circuit_half_open`
- `MOST-FN-599` — `resilience_circuit_close`
- `MOST-FN-600` — `resilience_bulkhead_acquire`
- `MOST-FN-601` — `resilience_bulkhead_release`
- `MOST-FN-602` — `resilience_fallback_select`
- `MOST-FN-603` — `resilience_health_probe`
- `MOST-FN-604` — `resilience_fault_inject`
- `MOST-FN-605` — `resilience_fault_seed_set`
- `MOST-FN-606` — `resilience_recovery_checkpoint`
- `MOST-FN-607` — `resilience_recovery_restore`
- `MOST-FN-608` — `resilience_shutdown_drain`
- `MOST-FN-609` — `resilience_shutdown_cancel`
- `MOST-FN-610` — `resilience_budget_report`

## Экосистема, интеграции и сопровождение — 21

`ecosystem-tooling` · Сборка, конфигурации, локализация, зависимости, ресурсы, диагностика, профилирование и федеративные интерфейсы.

### Экосистема, переносимость и разработка — 127–147

- `MOST-FN-127` — `мост собрать`
- `MOST-FN-128` — `словарь_переводов`
- `MOST-FN-129` — `аргументы_команды`
- `MOST-FN-130` — `конфиг_схема`
- `MOST-FN-131` — `лог_событие`
- `MOST-FN-132` — `при_остановке`
- `MOST-FN-133` — `изолированная_сборка`
- `MOST-FN-134` — `проверить_зависимости`
- `MOST-FN-135` — `карта_проекта`
- `MOST-FN-136` — `цель_размер`
- `MOST-FN-137` — `бенчмарк`
- `MOST-FN-138` — `мост формат`
- `MOST-FN-139` — `мост проверить`
- `MOST-FN-140` — `встроить_ресурс`
- `MOST-FN-141` — `планировщик_задач`
- `MOST-FN-142` — `отчет_ресурсов`
- `MOST-FN-143` — `c89 / c99 / c11 / c17`
- `MOST-FN-144` — `запуск_на_цели`
- `MOST-FN-145` — `режим_разбора`
- `MOST-FN-146` — `отчет_сбоя`
- `MOST-FN-147` — `состав_поведения`

## Status and evidence rules

The category view does not change implementation maturity. In registry edition `0.2-draft`:

- 666 entries have a written specification.
- 519 entries are marked `planned`.
- 134 entries are `specified_only`.
- 13 entries are `partial_outside_most`.
- 0 entries claim `most_native: true`.

A reference-runtime helper or an external project's implementation does not automatically mean the corresponding MOST callable exists. Status can advance only when the owning source, positive and negative tests, resource-bound checks, and target-specific acceptance evidence are present.

## Ownership

- `kernel-runtime`: DAK kernel/runtime contracts, with Reaper as the systems-language and policy owner.
- `language-compiler`: Reaper language, frontend, type system, compiler and toolchain.
- `desktop-ui`: Mora and the DAK native desktop track.
- `network-distributed`: DAK network services and Reaper protocol adapters.
- `storage-data`: DAK storage interfaces and Reaper data/serialization libraries.
- `security-resilience`: DAK security and BAV policy; enforcement must remain evidence-backed.
- `ecosystem-tooling`: Reaper tooling and versioned Ivan-VHS federation adapters.
