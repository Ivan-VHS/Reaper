# Reaper — мова програмування з композицією потоків даних

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="Python і native CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Reaper 0.1" src="https://img.shields.io/badge/Reaper-0.1.0-2563EB?style=flat-square">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/runtime-Python%203.10%2B-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-111827?style=flat-square">
</p>

<p align="center"><img src="assets/reaper-hero.svg" alt="Мова програмування Reaper з композицією потоків" width="100%"></p>

Reaper — незалежна мова програмування з композицією потоків даних, читабельним синтаксисом та обмеженим інтерпретатором. Інженерне дерево також містить переносимий фронтенд компілятора, підключувані host-runtime API та експериментальний напрям native C17. Інтерпретатор залишається еталоном семантики.

**Мови:** [English](README.md) · [Русский](README.ru.md) · Українська · [简体中文](README.zh-CN.md)

## Візуальний огляд

<p align="center"><img src="assets/reaper-toolchain-preview.svg" alt="Прев’ю фронтенду компілятора Reaper та шляху Quarry IR за вихідним кодом" width="100%"></p>
<p align="center"><img src="assets/reaper-nine-systems.svg" alt="Архітектура дев’яти обмежених host-runtime систем Reaper" width="100%"></p>

<sub>Це SVG-прев’ю, створені за вихідним кодом, і схема архітектури, а не скриншоти запущеного термінала. Текст термінала й значення у прев’ю є ілюстративними.</sub>

## Мова та runtime

- **Синтаксис потоків:** наявний оператор ~> поєднує перетворення без зміни граматики Reaper.
- **Інтерпретатор:** lexer, parser, AST та обмежене tree-walking виконання залишаються базовою моделлю сумісності.
- **Фронтенд компілятора:** консервативна статична діагностика, детермінований Quarry IR із прив’язкою до позицій у джерелі, структурна перевірка та безпечне згортання літералів. Машинний код не генерується.
- **Host-runtime API:** обмежені ресурсні області, асинхронні канали й actors, scoped-capabilities, контрольні знімки стану застосунку, локальна маршрутизація, profiling, capability-gated C ABI та спостереження за політикою здоров’я.
- **Звіт про платформу:** команда --target-info показує дані хоста, зокрема визначення E2K. Це не означає наявності native backend для MCST.
- **Native C17:** переносимі основи компілятора/runtime та тести розвиваються окремо від Python-інтерпретатора; повна паритетність мови не заявляється.

## Запуск прикладів

Потрібен Python 3.10 або новіший. Runtime використовує стандартну бібліотеку Python.

    git clone https://github.com/Ivan-VHS/Reaper.git
    cd Reaper
    python -m reaper --check examples/flow.rpr
    python -m reaper examples/flow.rpr
    python -m reaper --target-info
    python -m reaper.compiler_cli examples/flow.rpr --optimize

## Збирання та перевірка

Запуск Python-тестів:

    python -m compileall -q reaper tests
    python -m unittest discover -s tests -v

Збирання й тестування native C17:

    cmake -S . -B build -DBUILD_TESTING=ON
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

GitHub Actions перевіряє Python 3.10, 3.11 і 3.12, запускає приклади інтерпретатора, перевіряє CLI компілятора та приклад архітектури runtime, а також тестує native C17-цілі. Окремий HMGA workflow перевіряє інженерний контракт репозиторію.

## Об’єднані інженерні оновлення

Гілка інтеграції збирає сумісні зміни з відкритої історії розробки:

- **Фронтенд компілятора:** Quarry IR із прив’язкою до джерела, детерміновані хеші, консервативні статичні перевірки, структурна валідація та безпечне згортання констант.
- **Основи runtime:** обмежені ресурси, асинхронні канали/actors, scoped host-capabilities, контрольні знімки стану, локальна маршрутизація, profiling, обмежений C ABI та політика здоров’я.
- **E2K-профіль:** лише ідентифікація хоста й явний звіт про можливості; генерація native-коду MCST не реалізована.
- **Архітектура MOST:** поетапне узгодження системної архітектури з наявною мовою та міграцією C17 без зміни синтаксису Reaper.
- **HMGA v2/v3:** read-only аудит репозиторію та детермінований каталог із 20 аксіом і 400 операторів native C17 з кінцевим лімітом у 64 раунди.
- **Інженерні перевірки:** тести композиції з урахуванням сигнатур, перевірки версій Python, native C17 та задокументований процес review/merge.

Історичні прототипи з пересічними API actors, effects, ресурсів, relay і health перевірені та дедупліковані, а не встановлені поряд. Канонічним залишається поточний модульний набір host-runtime. Деталі наведені в [аудиті інтеграції](docs/INTEGRATION_AUDIT_2026-11-19.md).

## Архітектура та документація

- [Довідник мови](LANGUAGE.md)
- [Архітектура платформ](docs/PLATFORM_ARCHITECTURE.md)
- [Довідник дев’яти runtime-систем](docs/REAPER_SYSTEMS.md)
- [Архітектура циклічного runtime](docs/REAPERS_ARCHITECTURE.md)
- [Архітектура MOST](docs/MOST_SYSTEMS_ARCHITECTURE.md)
- [Інженерний стандарт](docs/ENGINEERING_STANDARD.md)
- [Контракт HMGA v2.0](docs/HMGA_V2.0.md)
- [Матриця операторів HMGA v3.0](docs/HMGA_V3.md)
- [Профіль хоста E2K](docs/ELBRUS_E2K.md)
- [Аудит інтеграції](docs/INTEGRATION_AUDIT_2026-11-19.md)

## Поточні межі

Reaper 0.1 залишається мовою з пріоритетом інтерпретатора. Фронтенд компілятора створює переносимий IR, а не машинний код. Host API явно підключаються на боці Python і не стають прихованими вбудованими можливостями мови чи пісочницею ОС. Генерація native-коду, JIT, розподілені actors, мережевий транспорт, cloud orchestration і повна підтримка MCST E2K не заявляються.

## Ліцензія

Проєкт поширюється за [Apache License 2.0](LICENSE).
