# MOST — расширение архитектуры: реестр 147 возможностей

**Статус:** архитектурный реестр и план реализации. Это не заявление о готовности всех перечисленных возможностей. На текущем этапе нативная ветка содержит лексическую основу MOST; парсер, типовая система, IR, анализ памяти и backend остаются отдельными этапами.

## Правила интеграции

1. Реестр продолжает базовую спецификацию из 66 правил. Нумерация ниже нормализована в семь непересекающихся диапазонов: 1–21, 22–41, 42–63, 64–84, 85–105, 106–126, 127–147. В исходном перечне раздел II содержит 20 пунктов, а раздел III — 22; поэтому утверждение «21 в каждом разделе» не совпадает с фактическим числом исходных пунктов. Все 147 пунктов сохранены без искусственного добавления или удаления.
2. Каждая функция должна иметь синтаксис, семантику, модель ошибок/эффектов, ограничения платформ, тесты и измеримый критерий приёмки до статуса implemented.
3. Ядро языка остаётся небольшим. Большинство возможностей — типизированные конструкции стандартной библиотеки или компиляторные атрибуты, а не новые ключевые слова.
4. Ни одна возможность не вводит скрытую аллокацию, неявный I/O, глобальные полномочия, фоновый поток или динамическое приведение.
5. Неопределённость и отказ выражаются типом `Result<T, E>`/суммарным типом ошибки. Бюджеты, таймауты, отмена и квоты возвращают явные состояния.
6. Все платформенные возможности имеют capability/target gate. Недоступная операция должна завершаться диагностикой сборки или явным `Unsupported`, а не фиктивной эмуляцией.
7. Оптимизации раскладки, SIMD, prefetch и lock-free допускаются только при сохранении наблюдаемой семантики и наличии fallback.
8. Названия ниже — предварительные русские имена API. Канонический ASCII/Unicode spelling, namespace и ABI будут утверждены в грамматике M1, чтобы не закреплять несовместимый синтаксис преждевременно.

## Реестр 147 функций

### I. Память, регионы и аппаратный уровень — 1–21

| № | Возможность | Проектный контракт / ограничение |
|---:|---|---|
| 1 | `снимок_региона` | Маркер отката arena/region; откат допустим только если ни одна ссылка на отменяемые аллокации не переживает снимок. |
| 2 | `бюджет_памяти` | Явная квота байтов на scope/вызов; превышение возвращает ошибку выделения, не аварийно завершает процесс. |
| 3 | `страница_ro` | Защита страниц через MMU там, где доступно; типовая неизменяемость остаётся обязательной и без MMU. |
| 4 | `стереть_при_освобождении` | Неустранимое secure-zero с compiler intrinsic и проверкой целевого backend; гарантия ограничена физикой/кэшем платформы. |
| 5 | `упаковать_по_доступности` | Необязательная оптимизация layout; запрещена для публичного ABI, сериализуемых и явно repr(C) структур. |
| 6 | `горячее / холодное` | Подсказки размещения basic blocks; корректность не зависит от подсказки. |
| 7 | `предзагрузка_шага` | Низкоуровневая подсказка prefetch; no-op на неподдерживаемых целях и не гарантия ускорения. |
| 8 | `кольцо_виртуальное` | Двойное отображение страниц только при поддержке ОС; fallback — обычный кольцевой буфер. |
| 9 | `порог_фрагментации` | Метрика allocator/region с определённой формулой; не обещает компактирование живых объектов. |
| 10 | `сид_размещения` | Детерминированный режим тестирования; production ASLR не ослабляется ради воспроизводимости. |
| 11 | `банк_памяти` | Явное размещение в target-defined memory spaces (SRAM/VRAM/shared); проверка доступности и выравнивания. |
| 12 | `dma_канал` | Типизированные DMA descriptors, pinning, alignment и ownership; аппаратные ограничения задаёт target description. |
| 13 | `лимит_кадров` | Статический/динамический предел рекурсии с типизированным отказом до переполнения стека. |
| 14 | `атомарно_сравнить_и_обновить` | CAS-loop только для типов с допустимым размером/alignment и явно заданным memory ordering. |
| 15 | `домен_безопасности` | Capability-контекст с deny-by-default; не выдаёт OS sandbox без соответствующей изоляции хоста. |
| 16 | `слот_потока` | Одноэлементный mailbox с формально определённым memory ordering и политикой overwrite/backpressure. |
| 17 | `размер_кадра_корутины` | Comptime/runtime метаданные размера async frame; лимит проверяется до запуска. |
| 18 | `пул_однотипных` | Фиксированный пул O(1), без системных вызовов после инициализации; исчерпание — явная ошибка. |
| 19 | `проверить_выравнивание` | Проверка alignment перед созданием typed pointer; не заменяет проверку размера/валидности объекта. |
| 20 | `разделить_по_смещению` | Zero-copy split slice с проверкой границ, alignment и endian/layout перед типизированным чтением. |
| 21 | `при_отмене` | Структурированная отмена с cleanup; гарантируется только для кооперативных cancellation points. |

### II. Типы, контракты и выразительность — 22–41

| № | Возможность | Проектный контракт / ограничение |
|---:|---|---|
| 22 | `уточнить_тип` | Refinement/newtype с проверяемым конструктором; после создания инвариант сохраняется всеми операциями. |
| 23 | `опционал_с_причиной` | Компактный tagged option/result; причина отсутствия имеет закрытый тип, не произвольную строку. |
| 24 | `одно_из` | Tagged union с ровно одним активным вариантом и exhaustive match. |
| 25 | `массив[N]` | Const-generic длина; несовпадение размерностей — ошибка типов. |
| 26 | `перечисление_с_правилом` | Типизированный конечный автомат; переходы доступны только через валидирующие функции. |
| 27 | `именованный_кортеж` | Структурно типизированный tuple с именами полей и стабильным правилом ABI. |
| 28 | `единицы_измерения` | Размерностные типы времени/скорости/пропускной способности; преобразования только явные или без потери точности. |
| 29 | `режим_округления` | Явная стратегия округления для каждой потенциально теряющей точность конверсии. |
| 30 | `насыщающий_и_модульный_тип` | Явно определённая арифметика типа; overflow semantics одинаковы на всех backend. |
| 31 | `инвариант` | Инварианты структуры проверяются на границах безопасных мутаций, а не после произвольной записи в raw-память. |
| 32 | `было(...)` | Snapshot старого значения в контрактах; копирование/сохранение ограничено типами и бюджетом. |
| 33 | `расширить` | Только доказуемо безопасные widening conversions; signedness и точность учитываются. |
| 34 | `ошибка_набора` | Вывод закрытого множества ошибок из call graph; публичные API фиксируют стабильный явный набор. |
| 35 | `фаза<T>` | Typestate для стадий инициализации; переход меняет тип и исключает недоступные операции. |
| 36 | `чистая` | Проверка отсутствия I/O, изменяемого внешнего состояния и недекларированных эффектов. |
| 37 | `без_аллокаций` | Транзитивный запрет heap/region allocation; stack/arena usage учитывается отдельно. |
| 38 | `ограничение_цикла` | Проверяемая мера продвижения/итерационный бюджет; общий termination proof не обещается. |
| 39 | `новый_тип` | Nominal newtype без неявного смешения с исходным типом. |
| 40 | `маска<T>` | Типизированные флаги с именованными битами, проверкой диапазона и операциями set/clear/test. |
| 41 | `локальный_тип` | Локальная область видимости типа; наружу не утечёт ни имя, ни layout без явного opaque handle. |

### III. Веб, UI и WASM — 42–63

| № | Возможность | Проектный контракт / ограничение |
|---:|---|---|
| 42 | `узел_dom` | Capability-bearing typed DOM handle; доступ только в браузерной цели и в пределах разрешённого root. |
| 43 | `вычислить_сигнал` | Memoized derived signal с явным графом зависимостей и удалением неиспользуемых подписок. |
| 44 | `пакет_сигналов` | Transaction/batch объединяет уведомления; наблюдатели видят согласованный снимок. |
| 45 | `список_по_ключу` | Keyed reconciliation только для списка конкретного UI-компонента, без Virtual DOM дерева приложения. |
| 46 | `кадр_рендера` | Координация requestAnimationFrame и бюджета кадра; графический API выбирается capability. |
| 47 | `форма_модель` | Typed form binding; parse/validation errors — данные, а не исключения. |
| 48 | `модуль_по_требованию` | Lazy WASM modules с версионированной typed ABI и проверкой целостности. |
| 49 | `оживить_при_видимости` | Visibility-triggered activation; fallback для сред без IntersectionObserver. |
| 50 | `состояние_в_url` | Типизированная двусторонняя сериализация разрешённых полей; секреты и большие состояния запрещены. |
| 51 | `хранилище_браузера` | IndexedDB/Cache Storage через capability; миграции схем версионированы и транзакционны. |
| 52 | `поток_в_ui` | Stream-to-view с backpressure и явной политикой throttling/drop. |
| 53 | `пружина` | Детерминированная модель spring animation; интегратор и timestep фиксированы/тестируемы. |
| 54 | `роль_доступности` | Семантические роли, label, focus и keyboard contracts; доступность проверяется статически где возможно. |
| 55 | `экран_ширина` | Typed responsive breakpoints; измерения доступны только в UI event/frame context. |
| 56 | `песочница_компонента` | Изоляция capabilities компонента; DOM sandbox/iframe применяется там, где нужна реальная граница безопасности. |
| 57 | `аудио_буфер_мост` | Web Audio buffers и realtime-safe DSP; audio callback не аллоцирует и не блокируется. |
| 58 | `очередь_офлайн` | Durable outbox с явной политикой повторов, дедупликации и разрешения конфликтов. |
| 59 | `метрики_интерфейса` | Web Vitals/frame metrics с opt-in сбором и privacy-safe режимом. |
| 60 | `маршрут` | Typed route definitions для client/server с единым набором параметров и ошибок валидации. |
| 61 | `жест` | Единая типизированная модель pointer/touch/keyboard input с отменой и capture semantics. |
| 62 | `сжать_кадр` | Typed binary frame codec для обмена данными; формат версионирован, ограничен по размеру и проверяется до декодирования. |
| 63 | `горячая_замена_модуля` | Dev-only hot replacement с проверкой совместимости typed ABI; в production hot swap выключен по умолчанию. |

### IV. Сеть и распределённые системы — 64–84

| № | Возможность | Проектный контракт / ограничение |
|---:|---|---|
| 64 | `протокол_кадр` | Декларативная схема пакета генерирует bounded parser/encoder с проверкой длины и endian. |
| 65 | `лимит_глубины_и_длины` | Бюджеты глубины, полей, элементов и суммарных байтов до аллокации. |
| 66 | `нуль_копий_сеть` | Borrowed buffers и ownership transfer; zero-copy — оптимизация, а не безусловная гарантия. |
| 67 | `с_таймаутом` | Deadline на операцию с монотонными часами и типизированным Timeout. |
| 68 | `повтор_с_откатом` | Retry только для явно идемпотентных операций, с cap, jitter и отменой. |
| 69 | `прерыватель` | Circuit breaker с конечными состояниями, метриками и явной политикой half-open. |
| 70 | `совместимость_схемы` | Проверка wire schema evolution и обратной/прямой совместимости в CI. |
| 71 | `контекст_трассировки` | Явный propagation context; отсутствие глобального ambient mutable context. |
| 72 | `пул_соединений` | Ограниченный пул с health check, timeout и детерминированным закрытием. |
| 73 | `ограничитель_частоты` | Token bucket/sliding window с монотонным временем и атомарным состоянием. |
| 74 | `ключ_идемпотентности` | Типизированный ключ и хранилище дедупликации с определённым TTL/объёмом. |
| 75 | `поток_чанков` | Chunk stream с bounded memory, backpressure и resume policy. |
| 76 | `сокет` | Unified TCP/UDP/Unix/TLS interface; TLS backend зависит от поддерживаемой криптографической реализации. |
| 77 | `контрольная_сумма<T>` | CRC/XXH для ошибок передачи/повреждения; криптографическую аутентичность не заменяет. |
| 78 | `возможности` | Передача минимального набора filesystem/network/process permissions как явных аргументов. |
| 79 | `логическое_время` | Lamport/vector clocks для причинного порядка; не подменяют физическое время. |
| 80 | `симуляция_сети` | Deterministic test transport с управляемыми loss, latency, reorder и disconnect. |
| 81 | `прочитать_безопасно` | Checked decoding с диапазонами, лимитами и отказом на неизвестных критичных значениях. |
| 82 | `канал_сообщений` | Typed pub/sub и request/reply с ограниченными очередями и backpressure. |
| 83 | `диспетчер_сообщений` | Exhaustive dispatch по message enum; неизвестные варианты обрабатываются явно. |
| 84 | `таймаут_медленного_чтения` | Header/body read deadlines и лимит минимальной скорости для сетевых серверов. |

### V. Компилятор, метапрограммирование и анализ — 85–105

| № | Возможность | Проектный контракт / ограничение |
|---:|---|---|
| 85 | `отражение_типа` | Comptime metadata полей/layout; приватные данные не раскрываются без разрешения модуля. |
| 86 | `дерево_синтаксиса` | Typed AST builder с валидацией и source provenance; произвольная текстовая подстановка запрещена. |
| 87 | `ошибка_компиляции / предупреждение_компиляции` | Структурированные compile-time diagnostics с точным source span. |
| 88 | `оценка_сложности` | Документируемые complexity contracts; доказательство O-оценки только для поддерживаемого подмножества. |
| 89 | `детектор_мертвого_кода` | Reachability/dead-field analysis с учётом reflection, exports и FFI roots. |
| 90 | `лимит_сложности` | Cyclomatic complexity threshold как lint/CI policy, не семантика языка. |
| 91 | `граф_зависимостей` | Циклы модулей и запрещённые архитектурные направления — ошибка проверки. |
| 92 | `мок_контракта` | Generated mock для trait с явной очередью результатов и записью вызовов. |
| 93 | `свойство_тест` | Property-based tests с фиксируемым seed, shrink strategy и воспроизводимым corpus. |
| 94 | `снимок_вывода` | Golden tests с явным обновлением эталона и нормализацией недетерминированных полей. |
| 95 | `бюджет_теста` | Time/allocation budgets с платформенным допуском и отчётом о variance. |
| 96 | `матрица_сборки` | CI matrix по target, feature flags, optimization и sanitizer configurations. |
| 97 | `причина_и_исправление` | Диагностика с причиной, span, related locations и безопасным machine-applicable fix. |
| 98 | `перемешать_с_сидом` | Seeded iteration order в тестах; production map iteration contract задаётся отдельно. |
| 99 | `неблокирующий_путь` | Effect analysis запрещает blocking calls в realtime/interrupt/UI-critical contexts. |
| 100 | `утверждение_доказуемое` | Ограниченный verifier пытается доказать утверждения; unknown не трактуется как proven. |
| 101 | `схема_типа` | Schema generation из типов с versioning и стабильным canonical representation. |
| 102 | `профиль_строк` | Source-mapped profiling; instrumentation включается явно и учитывает overhead. |
| 103 | `визуализация_памяти` | Отчёт region/borrow/move/drop graph из IR и CFG. |
| 104 | `не_ноль<T>` | NonZero refinement type для делителей и API, требующих ненулевое значение. |
| 105 | `сухой_прогон` | Effect journal/preview для поддерживаемых операций; внешние эффекты не применяются. |

### VI. Данные, текст и бинарные форматы — 106–126

| № | Возможность | Проектный контракт / ограничение |
|---:|---|---|
| 106 | `таблица_колонок` | SoA container с типизированными колонками и явной синхронизацией длины. |
| 107 | `битовый_набор` | Fixed/dynamic bitset с проверяемыми индексами и эффективными set operations. |
| 108 | `малый_вектор / малая_строка` | Inline capacity N; переход в heap/region только через явно объявленную политику overflow. |
| 109 | `поток_значений` | Lazy iterator pipeline без промежуточных коллекций и скрытых heap closures. |
| 110 | `парсер_среза` | Zero-copy parser с borrowed spans, абсолютными позициями и структурированными ошибками. |
| 111 | `разобрать_число` | Locale-independent numeric parser с radix/decimal policy и строгим диапазоном. |
| 112 | `путь_фс / путь_веб` | Разные path types; canonicalization и traversal prevention до открытия/маршрутизации. |
| 113 | `потоковый_разбор` | Incremental JSON/binary parser с bounded state и лимитами глубины/размера. |
| 114 | `префиксное_дерево` | Trie/prefix index с заданным allocator и memory budget. |
| 115 | `монотонный_тик / календарь_мгновение` | Отдельные monotonic и civil-time типы; календарные зоны — явные данные. |
| 116 | `ид_уникальный` | UUID/ULID-like identifiers с явно заданным источником entropy и гарантиями уникальности. |
| 117 | `сжать_поток / разжать_поток` | Streaming codecs с bounded output, checksum и защитой от decompression bombs. |
| 118 | `формат_строки` | Compile-time checked format strings; Unicode width/grapheme truncation отдельны от byte length. |
| 119 | `матрица / тензор` | Const-dimension algebra с проверкой размерностей и контролем overflow вычислений. |
| 120 | `квантовать / расквантовать` | Explicit scale/zero-point quantization с округлением и saturation policy. |
| 121 | `журнал_кольцо` | Fixed-capacity ring log; overwrite/drop policy и crash dump format определены. |
| 122 | `словарь<K,V>` | Deterministic iteration option и защита от hash flooding; seed/security mode задаются явно. |
| 123 | `сортировать_устойчиво` | Stable sort с гарантированной верхней границей времени и memory policy. |
| 124 | `найти_границу` | Overflow-safe lower/upper-bound search для монотонного предиката. |
| 125 | `канонизировать` | Canonical serialization с фиксированным порядком полей и нормализацией представления. |
| 126 | `регулярное_выражение` | Linear-time regex subset (например, Thompson NFA); backreferences и катастрофический backtracking исключены. |

### VII. Экосистема, переносимость и разработка — 127–147

| № | Возможность | Проектный контракт / ограничение |
|---:|---|---|
| 127 | `мост собрать` | Единая CLI entry point для native, WASM, firmware, library и server targets. |
| 128 | `словарь_переводов` | Compile-time completeness check по локалям; fallback policy задаётся явно. |
| 129 | `аргументы_команды` | CLI parser/help generation из typed parameter struct и validation contracts. |
| 130 | `конфиг_схема` | Typed config decoding, defaults, migrations и строгий отказ от неизвестных критичных полей. |
| 131 | `лог_событие` | Structured logging с уровнями, typed fields и compile-time filtering. |
| 132 | `при_остановке` | Graceful shutdown hooks с deadline и ограниченным временем cleanup. |
| 133 | `изолированная_сборка` | Hermetic build inputs, pinned toolchain, content hashes и отключённая сеть по умолчанию. |
| 134 | `проверить_зависимости` | Hash, provenance, license metadata и policy audit для git-pinned dependencies. |
| 135 | `карта_проекта` | Генерация графа модулей, вызовов, типов, размеров и entry points из compiler metadata. |
| 136 | `цель_размер` | Size-optimized profile, dead stripping, LTO и WASM/native size budgets. |
| 137 | `бенчмарк` | Benchmark harness с black-box result barrier, warmup, repetitions и статистикой. |
| 138 | `мост формат` | Канонический formatter; parser/formatter round-trip tests обязательны. |
| 139 | `мост проверить` | Архитектурные lint rules и policy checks в едином CI command. |
| 140 | `встроить_ресурс` | Compile-time resource embedding с типизированным byte slice и hash metadata. |
| 141 | `планировщик_задач` | Cross-target scheduler abstraction; threading/event-loop backend выбирается явно. |
| 142 | `отчет_ресурсов` | Debug resource ledger для регионов, файлов, сокетов и других linear handles. |
| 143 | `c89 / c99 / c11 / c17` | Ограниченные профили C header/declarator ingestion; макросы и препроцессор не исполняются произвольно. |
| 144 | `запуск_на_цели` | Интеграция с явно выбранным emulator/runner; поддерживаемые ISA и лицензии задокументированы. |
| 145 | `режим_разбора` | Explain mode для type inference, layout, effects, ownership и optimizer decisions. |
| 146 | `отчет_сбоя` | Versioned crash report с build id, stack trace и redaction-sensitive fields. |
| 147 | `состав_поведения` | Повторно подтверждённый архитектурный принцип: композиция контрактов вместо классового наследования. Реализация общая с функцией 42; это не отдельный механизм языка. |

## Разрешение пересечений и неоднозначностей

- Принцип композиции вместо наследования представлен только функцией 147; он реализуется через trait/contract composition и не требует второго отдельного механизма.
- Исходная функция 63 объединяла бинарную упаковку и hot replacement. В реализации это два независимых подсистемных API: codec в сетевом/data слое и hot reload только в dev runtime.
- `малый_вектор` не может незаметно переходить в heap: пользователь выбирает `fixed`, `region` или `fallible_heap` overflow policy.
- `страница_ro`, виртуальное кольцо, DMA, SIMD, prefetch и эмуляция зависят от target/OS и не могут быть обещаны одинаково на всех платформах.
- `сухой_прогон` применим только к операциям, которые проходят через контролируемый effect adapter; произвольный raw syscall нельзя безопасно «откатить».
- «Линейное время» regex относится к ограниченному формальному подмножеству, а не к любому синтаксису регулярных выражений.
- Криптографические хеши/CRC и защита от hash-flooding решают разные задачи; CRC не считается механизмом аутентификации.

## Очерёдность реализации

| Волна | Функции | Предпосылки и критерий выхода |
|---|---|---|
| A — Semantic base | 22–42, 85–87, 91, 97, 104 | Parser/AST, symbol resolution, typed IR, type/effect checker и устойчивые diagnostics. |
| B — Safe memory | 1–4, 9, 11–21, 37, 103, 142 | Region allocator, borrow/move analysis, cleanup CFG, sanitizer/property tests. |
| C — Data core | 25, 27–30, 39–40, 106–126 | Const generics, checked containers, parsers/codecs, fuzz corpus и complexity budgets. |
| D — Native systems | 5–8, 12–16, 64–84, 143–144 | Target descriptions, C ABI, socket/runtime layer, atomics, platform-specific tests. |
| E — WASM/UI | 43–63, 127, 136, 140–141 | WASM backend, typed browser host bindings, browser automation and XSS/a11y tests. |
| F — Toolchain | 85–105, 127–139, 145–146 | Formatter, test/fuzz/bench runner, reproducible builds, dependency audit and explain reports. |
| G — Stabilization | all public features | Compatibility corpus, ABI policy, performance baselines, threat model and versioned docs. |

## Implementation status

| Layer | Status |
|---|---|
| C17 lexical foundation and MOST token tests | Implemented in the feature branch |
| 147-feature architecture registry and constraints | This document |
| Parser/CST/AST | Not implemented |
| Name resolution and static type/effect checking | Not implemented |
| Typed IR and verifier | Not implemented |
| Region/borrow/linear ownership analysis | Not implemented |
| Native code generation | Not implemented |
| WASM code generation and browser host | Not implemented |
| Standard library/network/UI/runtime features | Not implemented |

The 147-item list is a traceable design backlog, not a claim that the language already provides those capabilities. A feature becomes **implemented** only when source syntax/API, semantics, backend behavior, documentation and executable acceptance tests are merged together.
