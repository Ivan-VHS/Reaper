# Reaper Processor Kernel v1

**Статус:** Reaper-native control-plane implementation, executable reference-runtime example; native backend, privileged kernel integration and physical hardware execution remain отдельными этапами.

## Назначение

Processor Kernel v1 — проверяемая модель управления процессорным ядром и связанными подсистемами Reaper. Это не эмулятор x86 и не драйвер. Слой задаёт единый язык состояний, ограниченное планирование задач, счётчики действий, воспроизводимые события, версии контрактов и компактное представление графов и таблиц.

Главный принцип: **каждое изменение имеет явное состояние, ограниченный шаг и проверяемый результат**. Время в контрольной модели — логические тики, а не обещание измерения реальной частоты CPU или задержки железа.

## Карта исходников

| Reaper source | Ответственность |
|---|---|
| `selfhost/kernel_state.rpr` | Lifecycle ядра, generation, logical tick, action counter, активные worker slots, fault reason |
| `selfhost/kernel_scheduler.rpr` | Bounded cooperative scheduler, приоритеты, round-robin для одинакового приоритета, block/wake/cancel |
| `selfhost/kernel_trace.rpr` | Последовательный event journal, монотонные logical ticks, replay-проверка |
| `selfhost/kernel_pulse.rpr` | Action pulse, dispatch/fault counters, live/peak memory и целочисленная скорость действий |
| `selfhost/kernel_version.rpr` | Трёхчастные версии, совместимость reader window, проверка каталога контрактов |
| `selfhost/kernel_graph.rpr` | Проверка DAG, поиск циклов, детерминированный topological order, компактирование без потери рёбер |
| `selfhost/kernel_table.rpr` | Схема колонок, контроль ширины строк и стабильный структурированный export |
| `selfhost/kernel_target.rpr` | Явный профиль CPU/ABI/OS/features/capabilities; никакого скрытого hardware probing |
| `examples/processor_kernel.rpr` | Сквозной пример и Reaper assertions |

Существующие низкоуровневые контракты остаются источниками истины для своих областей:

- `selfhost/memory_model.rpr` — учёт регионов, аллокаций, resize/release, лимитов и устаревших handles. Это ledger, а не управление физической памятью.
- `selfhost/ownership.rpr` — move/drop и проверка конфликтующих shared/mutable loans.
- `selfhost/hardware_contract.rpr` — MMIO descriptors, access policies, DMA ownership transitions и ограниченные IRQ effects. Функции проверяют контракты и не обращаются к шине.
- `stdlib/typed_registry.rpr` — типы, layout, target/ABI, effects и capability declarations.
- DABI64 v1 — pointer-free wire framing. Kernel syscall entry, IPC identity и аппаратные adapters остаются обязанностью доверенного host/OS слоя.

## Состояния ядра

Lifecycle v1:

`offline → booting → online → draining → halted`

Из `booting`, `online` и `draining` допускается переход в `faulted` по явной причине. Восстановление из `faulted` и перезапуск из `halted` начинаются с `booting`. Любая смена lifecycle увеличивает generation. Logical tick и action count монотонны в пределах экземпляра модели.
После fault worker slots нельзя считать очищенными автоматически. Их разрешено явно сверить и обнулить в состоянии `faulted` только после подтверждения доверенного host/OS слоя; переход к `booting` и `halted` блокируется, пока slots не равны нулю.

Нельзя записать action, пока ядро не находится в `online`. Нельзя перевести состояние в неизвестный lifecycle или оставить fault reason в здоровом состоянии. Для остановки сначала требуется вывести worker count в ноль; интеграция реального scheduler должна дополнительно доказать отсутствие активных задач и удерживаемых ресурсов.

## Модель многопоточности

Scheduler — детерминированная кооперативная модель задач, а не уже работающий SMP scheduler. Он ограничен 64 задачами. Задача имеет ID, имя, состояние, приоритет и конечный step budget. Каждый вызов dispatch потребляет ровно один logical step. Сначала выбирается максимальный приоритет; между задачами одного приоритета работает round-robin.
Event journal ограничен 100 000 событиями, pulse — 64 различными категориями, target profile — 128 feature и 128 capability entries. Таблица ограничена 64 колонками и 10 000 строками. Эти лимиты относятся к модели/контрактам, а не являются размером физической памяти ядра.

`block` принимает задачу только из ready, `wake` — только из blocked, `cancel` — только из ready/blocked. Завершённую или отменённую задачу нельзя запустить повторно. Прерывания, preemption, mutex implementation, атомарные инструкции и межъядерная синхронизация сюда пока не входят.

## Детерминизм и pulse

Event journal хранит возрастающий sequence number, kind, subject, canonical payload и logical tick. Временная шкала не может идти назад. Replay сравнивает ожидаемые записи с журналом без доступа к wall clock, RNG или сети. Хеширование произвольных payload и запись на диск относятся к отдельному serializer/storage контракту.

Pulse считает действия, dispatch, faults, live bytes и peak bytes. Скорость возвращается как целочисленная пара `[actions, elapsed_ticks]`; это не MHz, IPC, FLOPS или wall-clock throughput. Для реальных latency/throughput метрик нужен платформенный monotonic clock и отдельно проверенный profiler adapter.

## Графы, таблицы и версии

DAG принимает до 64 узлов и 256 рёбер. Компактирование строит детерминированный топологический порядок и переставляет рёбра, сохраняя их полный набор. Оно не выполняет transitive reduction и не удаляет зависимости.

Табличный export возвращает версионированное структурированное значение Reaper. Порядок строк сохраняется. Запись CSV/JSON/файла, подпись и контроль целостности — обязанности отдельного host adapter; молчаливой файловой записи нет.

Версионный контракт задаёт версию producer и допустимое окно reader. Это runtime/API compatibility, а не замена Git: историю исходников, теги, ветви и ревизии продолжает контролировать Git.

## Верификационные проверки

Сквозной пример проверяет:

- разрешённые и запрещённые переходы lifecycle;
- монотонность generation/tick/action count;
- приоритетную и round-robin выдачу задач и завершение по step budget;
- журналирование, replay и отклонение времени назад;
- pulse counters и целочисленное отношение действий к logical ticks;
- циклы DAG и сохранение рёбер при компактировании;
- несовместимые ABI/target профили и отказ в невыданной capability;
- schema/width checks и неизменность порядка экспортируемых строк.

Запуск через текущий Reaper bootstrap runtime:

```sh
python -m reaper --check examples/processor_kernel.rpr
python -m reaper examples/processor_kernel.rpr
```

Ожидаемая завершающая строка: `REAPER_PROCESSOR_KERNEL_V1_OK`. Проверка на reference runtime не доказывает native compiler parity, real thread execution, privileged kernel behavior или работу с физическим устройством.

## Следующие инженерные ворота

1. Подключить эти контракты к canonical IR и verifier, сохранив Span/SourceMap provenance.
2. Добавить ownership-aware task handles и проверку жизненного цикла locks, IRQ tokens и DMA buffers.
3. Реализовать runtime scheduler/atomics только после фиксации memory-order и cancellation contracts.
4. Подключить monotonic clock, profiler и hardware adapters через DABI64/OS capabilities.
5. Доказать native AOT parity, deterministic replay на нескольких targets и QEMU/hardware qualification.
6. Только после evidence переводить функции из Partial в Delivered.

Не считать файл, каталог или количество строк доказательством готовности подсистемы.
