# 100 Chinese Proverbs — engineering crosswalk for Reaper

Status: source-derived engineering guidance and review checklist. This document does not certify implementation or claim that every proverb is a software requirement.

## Scope

Reaper 0.1: Python-hosted expression language, lexer/parser/tree-walk runtime/CLI, explicit console effects and bounded execution.

For Reaper, translate each item into language semantics, lexer/parser/runtime contracts, explicit effects, quota enforcement, source diagnostics, CLI behavior and Python-host isolation.

The source contains 100 numbered proverb/idiom interpretations across four domains: architecture and data flow (1–25), resources and reliability (26–50), strategy and security (51–75), and collaboration and ecosystem (76–100). The table preserves all 100 source items in order. Repeated idioms in the source remain separate entries.

## Interpretation policy

- Treat the proverb as a mnemonic, not as a technical proof.
- Convert each metaphor into a measurable, testable requirement only when it fits this product.
- The source's claims about hardware wear, electrical behavior, TTL, processor registers, caching, distributed systems and performance are not accepted as universal facts; verify against actual platform specifications and measurements.
- Offensive examples (SQL injection, DDoS, honeypots, forged routing, zero-days, domain-controller takeover, deceptive traffic and malicious dependencies) are interpreted defensively: threat modelling, secure configuration, controlled test fixtures, least privilege and supply-chain review. Do not implement attack tooling or deploy deception against third parties.
- Irreversible operations require explicit authorization, backups/rollback where possible, and a recovery plan.
- Status remains **Review required** until linked to concrete source, test and CI evidence. No item becomes Implemented merely because it appears here.

## 100-item traceability ledger

| ID | Chinese proverb / idiom | Normalized engineering interpretation | Status |
|---:|---|---|---|
| 001 | 千里之行，始于足下 | Разбивать работу на малые проверяемые этапы; каждый этап имеет вход, выход и тест. | Review required |
| 002 | 水滴石穿 | Повторяющиеся операции измерять; накопительный износ и стоимость учитывать, а не романтизировать. | Review required |
| 003 | 百闻不如一见 | Диагноз подтверждать воспроизводимым тестом, дампом или измерением, а не предположением. | Review required |
| 004 | 稳扎稳打 | Предпочитать надёжную фиксацию состояния и проверяемые операции рискованным оптимизациям. | Review required |
| 005 | 不怕慢，就怕站 | Долгие операции должны иметь прогресс, тайм-аут или отмену; зависание недопустимо. | Review required |
| 006 | 机会留给有准备的人 | Заранее резервировать и проверять ресурсы; ошибки выделения обрабатывать явно. | Review required |
| 007 | 百闻不如一见 | Отладку выполнять на актуальном коде и воспроизводимом окружении. | Review required |
| 008 | 聚沙成塔 | Собирать продукт из небольших модулей с ясными контрактами. | Review required |
| 009 | 人外有人，天外有天 | Не обещать производительность выше измеренных ограничений платформы. | Review required |
| 010 | 十年树木，百年树人 | Долгоживущие данные и API изменять миграциями и с обратной совместимостью. | Review required |
| 011 | 欲速则不达 | Оптимизации не должны отключать проверки корректности и безопасности. | Review required |
| 012 | 水往低处流 | Потоки данных и управления направлять через явные, документированные границы. | Review required |
| 013 | 覆水难收 | Необратимые изменения отделять от подготовки; предусматривать откат или компенсацию. | Review required |
| 014 | 强弩之末 | Учитывать бюджеты времени, TTL, глубину вызовов и срок жизни ресурсов. | Review required |
| 015 | 树倒猢狲散 | Обрабатывать отказ центрального компонента и деградацию зависимых частей. | Review required |
| 016 | 盲人摸象 | Модульные тесты дополнять интеграционными сценариями. | Review required |
| 017 | 天高皇帝远 | Учитывать задержки и недоступность внешних зависимостей; локальный режим не должен зависеть от сети. | Review required |
| 018 | 刻舟求剑 | Не использовать устаревшие указатели, кэшированные предположения и сведения о платформе. | Review required |
| 019 | 揠苗助长 | Не форсировать частоты, параллелизм или рост данных без измерений и ресурсных ограничений. | Review required |
| 020 | 画蛇添足 | Избегать лишних абстракций и функций без конкретного сценария. | Review required |
| 021 | 守株待兔 | Не заменять событийную модель бесконечным опросом. | Review required |
| 022 | 掩耳盗铃 | Не подавлять предупреждения, ошибки линтера и сигналы мониторинга. | Review required |
| 023 | 严于律人，宽于律己 | Проверять собственные границы и входы до обвинения внешних библиотек. | Review required |
| 024 | 滥竽充数 | Не оставлять заглушки под видом реализованной функции. | Review required |
| 025 | 铁杵磨成针 | Оптимизировать микродетали только после профилирования. | Review required |
| 026 | 纸里包不住火 | Утечки памяти, дескрипторов и ресурсов должны обнаруживаться тестами. | Review required |
| 027 | 星星之火，可以燎原 | Проверять, как единичная ошибка или уязвимость влияет на весь продукт. | Review required |
| 028 | 树大招风 | Защищать публичные интерфейсы от перегрузки и злоупотреблений. | Review required |
| 029 | 疾风知劲草 | Проверять устойчивость при отказах и нестабильных входах. | Review required |
| 030 | 一山不容二虎 | Исключать гонки за эксклюзивные ресурсы и неявное совместное владение. | Review required |
| 031 | 掘井九仞而不及泉 | Не считать сборку завершённой без линковки, тестов и запуска. | Review required |
| 032 | 空罐子响得最响 | Логи должны быть содержательными, ограниченными и не подменять функциональность. | Review required |
| 033 | 九层之台，起于累土 | Конфигурация и развёртывание должны начинаться с минимального валидного состояния. | Review required |
| 034 | 覆水难收 | Физическое удаление и изменение пользовательских данных требует явного подтверждения и восстановления. | Review required |
| 035 | 冰冻三尺，非一日之寒 | Технический долг отслеживать как накопительный риск. | Review required |
| 036 | 不到黄河心不死 | Профилировать полный путь выполнения, а не только очевидный участок. | Review required |
| 037 | 抱薪救火 | Не лечить нехватку памяти бесконтрольным увеличением swap или лимитов. | Review required |
| 038 | 釜底抽薪 | Устранять источник чрезмерной нагрузки, а не только симптомы. | Review required |
| 039 | 物极必反 | Устанавливать верхние границы нагрузки и проверять перегрузку. | Review required |
| 040 | 千里之堤，溃于蚁穴 | Проверять малые граничные случаи, переполнения и некорректные символы. | Review required |
| 041 | 防患于未然 | Включать статический анализ и проверки до выпуска. | Review required |
| 042 | 良药苦口利于病 | Строгие проверки и типовые ограничения предпочтительнее скрытой неоднозначности. | Review required |
| 043 | 病从口入，祸从口出 | Валидировать внешние входы и экранировать вывод. | Review required |
| 044 | 流水不腐 | Периодически очищать временные ресурсы и ограничивать рост журналов. | Review required |
| 045 | 户枢不蠹 | Поддерживать обслуживаемость через регулярные тесты и обновления зависимостей. | Review required |
| 046 | 怒伤肝，悲伤肺 | Избегать циклов перегрева и чрезмерной нагрузки; телеметрию не выдумывать. | Review required |
| 047 | 饭吃七分饱 | Оставлять запас памяти и CPU для ОС и интерактивной работы. | Review required |
| 048 | 头痛医头，脚痛医脚 | Исправлять первопричину, сохраняя регрессионный тест. | Review required |
| 049 | 人不能两次踏入同一条河流 | Не предполагать детерминизм многопоточного и внешне зависимого состояния без контроля входов. | Review required |
| 050 | 滴水穿石，铁杵成针 | Рефакторить итеративно, сохраняя поведенческую эквивалентность тестами. | Review required |
| 051 | 不战而屈人之兵 | Упрощать алгоритм до устранения ненужной работы, если это доказано. | Review required |
| 052 | 知己知彼，百战不殆 | Профилировать собственный код и учитывать реальные свойства окружения. | Review required |
| 053 | 韬光养晦 | Не раскрывать внутренние детали и чувствительные данные в диагностике. | Review required |
| 054 | 借刀杀人 | Делегировать тяжёлую работу специализированному адаптеру только через явный контракт. | Review required |
| 055 | 鹬蚌相争，渔翁得利 | Разбирать взаимные блокировки и конкуренцию за ресурсы. | Review required |
| 056 | 前门拒虎，后门进狼 | Проверять все входные точки, включая отладочные и вспомогательные. | Review required |
| 057 | 空城计 | Ловушки и имитация атак допустимы только в изолированных тестах защиты; не в рабочем продукте. | Review required |
| 058 | 围魏救赵 | При инциденте защищать критический путь и переключаться на проверенный резерв. | Review required |
| 059 | 明修栈道，暗度陈仓 | Запрещать скрытые изменения протоколов; миграции должны быть объявлены и совместимы. | Review required |
| 060 | 以逸待劳 | Использовать ограниченные пулы и повторное использование ресурсов вместо бесконтрольного создания потоков. | Review required |
| 061 | 破釜沉舟 | Не удалять откат без утверждённого плана восстановления и тестов миграции. | Review required |
| 062 | 笑里藏刀 | Проверять зависимости, цепочку поставки и происхождение изменений. | Review required |
| 063 | 李代桃僵 | Изолировать вспомогательные компоненты так, чтобы их отказ не повредил ядро. | Review required |
| 064 | 趁火打劫 | Не эксплуатировать уязвимости; моделировать угрозы и закрывать окна обновления. | Review required |
| 065 | 声东击西 | Тестировать устойчивость обнаружения на ложных сигналах только в контролируемой среде. | Review required |
| 066 | 擒贼先擒王 | При аварии локализовать первопричину и критическую точку отказа. | Review required |
| 067 | 围师必阙 | Предусматривать безопасное прерывание, отмену и восстановление сессии. | Review required |
| 068 | 反间计 | Проверять подлинность сообщений, метаданные и границы доверия. | Review required |
| 069 | 三十六计，走为上计 | При отказе безопасно завершать работу или переключаться на резерв. | Review required |
| 070 | 苦肉计 | Замедление и fault injection применять только в тестовом контуре с лимитами. | Review required |
| 071 | 斩草除根 | Удалять неиспользуемые зависимости после проверки графа и совместимости. | Review required |
| 072 | 杀鸡儆猴 | Не использовать разрушительные демонстрации; применять изолированные тесты и правила качества. | Review required |
| 073 | 抛砖引玉 | Открывать интерфейсы и документацию для внешнего вклада с ревью и тестами. | Review required |
| 074 | 断其粮道 | Ограничивать полномочия и сетевой доступ по принципу минимально необходимого. | Review required |
| 075 | 将怒失智 | Аварийные административные действия требуют подтверждения, журнала и безопасного отказа. | Review required |
| 076 | 一言既出，驷马难追 | Публичные API, релизы и сетевые операции считать контрактами с последствиями. | Review required |
| 077 | 三人成虎 | Не принимать слухи о дефекте без воспроизводимого доказательства. | Review required |
| 078 | 物以类聚，人以群分 | Группировать данные по явной схеме и проверенным признакам. | Review required |
| 079 | 船多打顶，人多乱行 | Назначать владельцев модулей и единые правила интеграции. | Review required |
| 080 | 上梁不正下梁歪 | Исправлять архитектурные дефекты в основании, а не маскировать их в адаптерах. | Review required |
| 081 | 雪中送炭 | При дефиците ресурсов включать предсказуемую деградацию и приоритеты. | Review required |
| 082 | 授人以鱼不如授人以渔 | Документировать причины и процедуры, чтобы разработчик мог сам диагностировать систему. | Review required |
| 083 | 君子之交淡如水 | Предпочитать слабую связанность и stateless-интерфейсы там, где это оправдано. | Review required |
| 084 | 名誉扫地 | Считать утечку данных и нарушение доверия критическими инцидентами. | Review required |
| 085 | 林子大了，什么鸟都有 | Считать внешние вклады недоверенными до ревью и проверки. | Review required |
| 086 | 入乡随俗 | Соблюдать соглашения репозитория и платформы, фиксируя исключения. | Review required |
| 087 | 螳臂当车 | Согласовывать вычислительную задачу с реальными возможностями целевой платформы. | Review required |
| 088 | 退一步海阔天空 | Упрощать чрезмерно сложный дизайн, сохраняя совместимость. | Review required |
| 089 | 三个臭皮匠，顶个诸葛亮 | Использовать независимое ревью и коллективную проверку. | Review required |
| 090 | 一人耕田，七人吃饭 | Балансировать производительность компонентов и выявлять очереди/простои. | Review required |
| 091 | 老好人 | Не делать один универсальный интерфейс ценой неоднозначности и безопасности. | Review required |
| 092 | 富不过三代 | Планировать сопровождение, миграции и удаление устаревшего кода. | Review required |
| 093 | 兼听则明，偏信则暗 | Учитывать результаты CI, ревью, тестов и пользовательских отчётов. | Review required |
| 094 | 同舟共济 | Координировать разработку, тестирование и сопровождение во время инцидента. | Review required |
| 095 | 水能载舟，亦能覆舟 | Учитывать обратную связь и нагрузку пользователей как источник и ценности, и риска. | Review required |
| 096 | 家丑不可外扬 | Расследовать инциденты ответственно, но не скрывать обязательные уведомления и факты от затронутых сторон. | Review required |
| 097 | 同甘共苦 | Разделять ответственность за устранение инцидента и фиксировать действия. | Review required |
| 098 | 夏虫不可语冰 | Подбирать документацию под уровень читателя, не упрощая факты. | Review required |
| 099 | 杀鸡取卵 | Не отключать наблюдаемость и тесты ради краткосрочной экономии. | Review required |
| 100 | 金玉其外，败絮其中 | Сверять README, интерфейсы и заявления с реально работающим кодом. | Review required |

## Project-specific application

### Architecture and data flow (001–025)
- Keep lexer, parser, runtime and CLI as separate stages with explicit token/AST/value contracts.
- Keep language effects explicit; ordinary expressions must not gain ambient filesystem, network, process or hardware access.
- Both: test full workflows in addition to unit-level components; avoid speculative abstractions and unmeasured optimization.

### Resource and reliability (026–050)
- Apply consistent limits to source, tokens, nesting, steps, call depth, collections and generated text; translate host failures into language diagnostics.
- Both: measure resource use, reserve headroom, test boundary conditions, and preserve regression tests for every fixed defect.

### Security and failure strategy (051–075)
- Do not claim sandboxing. Keep host effects explicit and do not execute untrusted programs as privileged workloads.
- Both: validate all boundaries, review dependency provenance, test recovery and cancellation, and keep offensive scenarios inside isolated defensive test environments.

### Collaboration and ecosystem (076–100)
- Keep LANGUAGE.md, README, grammar, runtime and examples aligned; run the supported Python-version test matrix.
- Both: require independent review, reproducible builds/tests, clear ownership and transparent incident handling.

## Acceptance gate

A ledger item may move from Review required to Partial or Implemented only when its PR records:
1. the exact item ID and product-specific rationale;
2. the affected source files and public contract;
3. a regression, boundary, integration or security test;
4. the exact CI run and commit SHA;
5. any non-applicability decision and its reason.

Do not use this crosswalk to justify disabling checks, hiding incidents, bypassing review, or making unverified hardware/performance/security claims.
