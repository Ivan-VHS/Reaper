# Reaper — UI/UX implementation profile

**Shared standard:** [UI/UX Codex 40026](https://github.com/Ivan-VHS/DAK/blob/main/docs/UI_UX_CODEX_40026.md).

This file keeps only the Reaper Studio toolkit notes. The shared specification owns common interaction rules, accessibility budgets, theme/component contracts and the definition of done.

### Reaper Studio — локальная реализация

- Редактор и диагностический контекст остаются главным визуальным доминантом; инструменты и редко используемые команды не перехватывают место исходного текста.
- Контракт клавиатуры сохраняет существующие Ctrl+O, Ctrl+S, F5, Shift+F5 и F9; тестируются Tab/Shift+Tab, Esc и возврат фокуса из диалогов.
- В Tk теме все варианты Light/Dark/Dawn/Sunset/Night обязаны проходить проверку контраста для текста, поверхностей, выделения и надписей на action-кнопках.
- Motion и status feedback не должны изменять позицию курсора, выделение документа или время выполнения кода.
- Конкретные IDE-команды и диагностика сохраняются отдельными от визуальных режимов; отсутствие функции не маскируется неактивной кнопкой без пояснения.
