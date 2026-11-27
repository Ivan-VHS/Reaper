# Neural Systems Contract v1

**Canonical owner:** Reaper  
**Source of truth:** stdlib/neural_systems.rpr  
**Conformance fixture:** examples/neural_systems.rpr  
**Maturity:** bounded reference-runtime implementation; native AOT, GPU and distributed training parity are not claimed.

## Purpose

Neural Systems v1 gives the DAK/Reaper ecosystem one deterministic neural-model contract and twenty named architectural profiles. The three labels in each profile identify a model family, its contract vocabulary and its engineering scope. They are complementary profiles of one system, not twenty unrelated runtimes.

The core currently implements dense feed-forward inference and bounded online/batch stochastic-gradient training in Reaper source. Model data is explicit, input values are not modified, and training returns a new model value.

## Mathematical model

For layer l:

\[
z^{(l)} = W^{(l)} a^{(l-1)} + b^{(l)}, \qquad
a^{(l)} = \phi_l(z^{(l)}), \qquad a^{(0)}=x
\]

The supported activations are linear, ReLU and leaky ReLU. The training loss is mean half-squared error. Back-propagation computes output and hidden-layer deltas, normalizes the output error by vector width, then applies:

\[
W^{(l)} \leftarrow W^{(l)}-\eta\,\delta^{(l)}(a^{(l-1)})^T,\qquad
b^{(l)} \leftarrow b^{(l)}-\eta\,\delta^{(l)}
\]

Batch order is fixed. No hidden shuffling, random seed, clock, file access, network request, device access or host callback is used by this reference implementation.

## Versioned model and execution contract

A model is the seven-field record produced by network(...):

1. schema identifier reaper.neural-network.v1;
2. layer widths, including input and output;
3. one output-major weight matrix per dense layer;
4. one bias vector per dense layer;
5. one activation name per dense layer;
6. learning rate in (0,1];
7. maximum training-step budget.

A contract produced by make_contract(...) fixes the profile labels, execution mode, deterministic requirement, local-only data policy, sample budget, step budget and external-export flag. The v1 validator rejects any contract that is not deterministic and local-only.

| Bound | v1 limit |
|---|---:|
| Dense layers | 1–8 |
| Units per layer | 1–512 |
| Trainable parameters | 65,536 |
| Samples per batch | 1–1,024 |
| Epochs per batch | 1–1,000 |
| Training steps declared by model | 1–1,000,000 |
| Numeric input, weight and bias magnitude | 1,000,000 |

Invalid dimensions, malformed layers, unsupported activation functions, invalid numeric values and work beyond the declared budget are rejected before training or inference.

## Twenty architectural profiles

| # | Neural model | Contract | Engineering scope |
|---:|---|---|---|
| 1 | Искусственная нейронная сеть | Нейросетевой контракт | Системное проектирование |
| 2 | Нейронная сеть | Нейросетевое соглашение | Системное конструирование |
| 3 | ИНС | Сетевой нейродоговор | Системное программирование |
| 4 | Нейронная модель | Нейронный контракт | Комплексная разработка |
| 5 | Искусственный интеллект | Цифровой нейроконтракт | Архитектурная разработка |
| 6 | Интеллектуальная система | Интеллектуальный контракт | Инженерная разработка |
| 7 | Машинная модель | Когнитивный контракт | Комплексное проектирование |
| 8 | Вычислительная сеть | Искусственно-интеллектуальный контракт | Разработка систем |
| 9 | Когнитивная система | Автономный нейроконтракт | Создание систем |
| 10 | Интеллектуальная модель | Распределённый нейроконтракт | Системная инженерия |
| 11 | Обучаемая система | Децентрализованный нейроконтракт | Архитектурное проектирование |
| 12 | Самообучающаяся модель | Машинный нейроконтракт | Технологическая разработка |
| 13 | Алгоритмическая сеть | Нейросетевой договор | Интеграционная разработка |
| 14 | Цифровой интеллект | Интеллектуальное соглашение | Модульная разработка |
| 15 | Машинный интеллект | Цифровой нейродоговор | Многоуровневая разработка |
| 16 | Генеративная модель | Нейросетевое обязательство | Платформенная разработка |
| 17 | Нейрокомпьютерная система | Сетевой интеллектуальный договор | Инфраструктурная разработка |
| 18 | Программный интеллект | Автономное нейросетевое соглашение | Системное моделирование |
| 19 | Адаптивная модель | Распределённое нейросетевое соглашение | Проектирование архитектуры |
| 20 | Искусственный разум | Программируемый нейроконтракт | Комплексная системная инженерия |

The source exports profile_catalog() as the canonical owner of all twenty labels. The fixture verifies its size and checks that labels are unique in their respective columns.

## Federation responsibilities

| Repository | Reaper-side responsibility |
|---|---|
| Reaper | Canonical model representation, validation, inference, training and contract catalog |
| DAK | User-space service admission, bounded memory/step budgets and capability-deny policy |
| Pytyliki | Read-only processor/resource evidence and deterministic capacity recommendations |
| OPlague | Local device/driver evidence triage; review-only recommendations, never driver installation |
| VentuSample | Offline audio-model profile validation; no real-time DSP callback or external audio upload |

The adapters validate requests and evidence. They do not copy the neural engine or silently grant host capabilities. Each project retains its native implementation and existing ABI.

## Safety and maturity boundaries

- Local data only is the default. External export requires a separate explicit contract and is rejected by the v1 helper.
- The Reaper implementation is executed by the current reference runtime. The current native AOT subset does not cover these list and dynamic collection operations.
- No CUDA/Vulkan/GPU backend, distributed parameter server, model marketplace, autonomous deployment or cryptographic model-signature verifier is implemented here.
- The DAK adapter is a user-space admission plan, not a kernel scheduler or hard memory isolation mechanism.
- Pytyliki recommendations are based on supplied evidence; they do not tune frequency, voltage, affinity, firmware or drivers.
- OPlague remains read-only and dry-run by default.
- VentuSample remains deterministic offline audio software; neural work is not run in an audio callback and does not claim a real-time DAW.
- This is not a safety-critical, clinical, financial or security-certification model.

## Verification

The Reaper CI workflow checks and executes examples/neural_systems.rpr through the reference runtime. The fixture covers 20-profile uniqueness, dense inference, hidden ReLU inference, deterministic SGD, bounded batch training, shape errors, rejected execution modes and local-only contract enforcement.
