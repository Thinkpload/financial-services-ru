# Управление ветками форка

Форк `Thinkpload/financial-services-ru` от `anthropics/financial-services`. Адаптация под РФ 2026 (РСБУ, 152-ФЗ, ИТ-аккредитация, M&A ИТ-аутсорс).

## Структура

| Что | Где | Назначение |
|---|---|---|
| `upstream` | remote → `anthropics/financial-services` | Источник обновлений Anthropic. Только `fetch/pull`, никогда `push`. |
| `origin` | remote → `Thinkpload/financial-services-ru` | Наш fork на GitHub. |
| `main` | local + `origin/main` | Зеркало `upstream/main`. **Никаких правок напрямую.** |
| `ru-work` | local + `origin/ru-work` | Единственная рабочая ветка. Вся адаптация под РФ — здесь. |

## Remotes (проверка)

```bash
git remote -v
# origin    https://github.com/Thinkpload/financial-services-ru (fetch/push)
# upstream  https://github.com/anthropics/financial-services.git (fetch/push)
```

Если `upstream` отсутствует:
```bash
git remote add upstream https://github.com/anthropics/financial-services.git
```

## Ежедневная работа

Все коммиты — в `ru-work`:
```bash
git checkout ru-work
# ... правки ...
git add <files>
git commit -m "..."
git push origin ru-work
```

## Подтягивание обновлений из апстрима

Когда Anthropic выкатывает новое в `upstream/main`:

```bash
# 1. Обновляем локальный main из апстрима
git checkout main
git pull upstream main
git push origin main          # синхронизируем fork на GitHub

# 2. Вливаем свежий main в рабочую ветку
git checkout ru-work
git merge main                # либо: git rebase main
# ... разрешаем конфликты, если есть ...
git push origin ru-work
```

**Merge vs rebase:** `merge` сохраняет историю как есть (безопаснее, рекомендую). `rebase` даёт линейную историю, но переписывает коммиты — не делай rebase, если `ru-work` уже запушена и кто-то с неё работает.

## Что НЕ делать

- ❌ Не коммитить в `main` напрямую — он должен оставаться чистым зеркалом апстрима.
- ❌ Не пушить в `upstream` — нет прав, и не нужно.
- ❌ Не плодить ветки `ru/feature-X` без необходимости. Решили: одна `ru-work`.
- ❌ Не делать `git push --force` в `ru-work` без явной причины.

## Если что-то сломалось

**`ru-work` разъехалась с `main` сильно, конфликты при merge:**
- Решаем конфликты руками файл за файлом. Наши правки скиллов под РСБУ имеют приоритет — апстримовые US-GAAP версии перекрываем.

**Случайно закоммитил в `main`:**
```bash
git checkout main
git reset --hard upstream/main    # откатить main к апстриму
git checkout ru-work
git cherry-pick <hash>            # перенести коммит в рабочую ветку
```

**Хочу посмотреть, что нового в апстриме перед мерджем:**
```bash
git fetch upstream
git log main..upstream/main --oneline
```

## Стратегия адаптации (контекст для веток)

Правки идут в `plugins/vertical-plugins/<vertical>/skills/<skill>/` — это источник. После правок:
```bash
python3 scripts/sync-agent-skills.py   # синхронизирует копии в agent-plugins/
python3 scripts/check.py               # валидация манифестов
```

Pre-commit hook сам патч-бампит `version` в `plugin.json` затронутых плагинов.

## Релиз (когда захотим)

Когда `ru-work` стабильна и готова к использованию командой — мерджим её в `origin/main` через PR на GitHub (`Thinkpload/financial-services-ru`, base: `main`, compare: `ru-work`). `origin/main` к этому моменту уже отличается от `upstream/main` нашими правками — это нормально для долгоживущего форка.
