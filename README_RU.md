# Quote Guard — предохранитель, который не даёт агенту повесить собственный шелл

> 📖 **Читать полную трилогию экспериментов (1 416 канонических проб):** [The Ghost in the Context Window (PDF)](The_Ghost_in_the_Context_Window_Trilogy.pdf)

**🇷🇺 Русский** | [ 🇬🇧 Read in English ](README.md)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23813780.svg)](https://doi.org/10.5281/zenodo.23813780)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0005--7773--3581-green.svg)](https://orcid.org/0009-0005-7773-3581)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/skywhiteangels-cell/llm-token-architect/actions/workflows/tests.yml/badge.svg)](https://github.com/skywhiteangels-cell/llm-token-architect/actions)
[![Tests](https://img.shields.io/badge/tests-134%20passing-brightgreen)](#тесты)
[![Read in English](https://img.shields.io/badge/Read_in-English-blue.svg)](README.md)

![Обложка](habr_cover.jpg)

Автономный агент теряет закрывающую кавычку. Команда уходит в PowerShell с
нечётным числом `"`. Шелл решает, что пользователь ещё не закончил ввод, рисует
`>>` и засыпает навсегда. Читать stderr нечего, кода ошибки для самокоррекции
нет — цикл агента просто мёртв, сессию приходится перезапускать руками.

Этот репозиторий — **детерминированная проверка перед запуском** ровно на такой
случай: она читает строку команды, проходит её так, как это сделал бы лексер
шелла, и отказывается запускать, если на конце строки остался незакрытый
контекст кавычки, бэктика или переноса строки.

Два файла, ноль зависимостей, один код возврата.

## Опубликованные работы

| | Работа | DOI | Язык |
|---|---|---|---|
| 1 | [The Ghost in the Context Window](https://doi.org/10.5281/zenodo.23679671) — трилогия об исследовании | `10.5281/zenodo.23679671` | русский |
| 2 | [The Attention Dispersion Law and Dual-Path Decoupling in Autoregressive Transformers](https://doi.org/10.5281/zenodo.23813780) — препринт | `10.5281/zenodo.23813780` | английский · русский |
| 3 | [Deterministic Audit of LLM-Generated Research Claims](https://doi.org/10.5281/zenodo.23817684) — протокол аудита | `10.5281/zenodo.23817684` | английский · русский |

Запись 3 аудирует утверждения записи 2; запись 1 — популярное изложение, написанное
в конце той же сессии. Все три связаны на Zenodo в обе стороны.

Если используете код — цитируйте этот репозиторий. Если ссылаетесь на результаты —
запись 2; оба варианта лежат в [`CITATION.cff`](CITATION.cff).


## Быстрый старт

```bash
# CLI
python parity_check.py -c 'echo "hi' --shell posix
# -> PARITY VIOLATION — unterminated double context opened at offset 5
#    код возврата 1

node parity_check.js -c 'echo hi' --shell powershell
# -> PARITY OK — command is safe to execute.   код возврата 0
```

```python
from parity_check import verify_quote_parity, analyze

verify_quote_parity('echo "it\'s a test"', shell="posix")       # True  — валидно, ложного срабатывания нет
verify_quote_parity('dir "C:\\"',          shell="posix")       # False — в bash \ экранирует кавычку
verify_quote_parity('dir "C:\\"',          shell="powershell")  # True  — в PS \ литерален

analyze('echo "hi', shell="posix")
# {'safe': False, 'state': 'DOUBLE', 'shell': 'posix',
#  'reason': 'unterminated double context opened at offset 5', 'offset': 5}
```

```javascript
const { verifyQuoteParity, analyze } = require('./parity_check');
verifyQuoteParity('echo "hi', 'powershell');   // false
```

Коды возврата: `0` — безопасно · `1` — повиснет · `2` — ошибка вызова.

## Грамматика шелла — не опция

Именно на этом ломается большинство предохранителей, и именно поэтому здесь три
грамматики, а не одна.

| Шелл | Escape-символ | Кавычки | Следствие |
|---|---|---|---|
| `posix` (bash, sh, zsh, Git Bash) | `\` | `'...'`, `"..."`, `` `...` `` | `dir "C:\"` **повиснет** — `\` экранирует кавычку |
| `powershell` (5.1 / 7+) | `` ` `` | `'...'` литерально, `''` и `""` дают литерал | `dir "C:\"` **валидно** — `\` литерален |
| `cmd` (cmd.exe) | `^` | только `"..."` | `echo ^"hi` валидно |

Одна и та же строка получает разные вердикты в разных грамматиках. Это не баг, а
суть: проверка, которая применяет правила POSIX на Windows, блокирует рабочие
команды. А предохранитель, блокирующий рабочие команды, выключают.

По умолчанию — `posix`. Для PowerShell на Windows передавайте `--shell powershell`
явно.

## Что ловит

- незакрытые `"` и `'` во всех трёх грамматиках
- незакрытую подстановку бэктиком (POSIX)
- висящий escape в конце строки — одиночный `\`, `` ` `` или `^`: это перенос
  строки, и он вешает шелл так же надёжно, как открытая кавычка
- ложное срабатывание на `echo "it's a test"`, которое даёт наивный подсчёт чётности
- при этом корректно понимает удвоение `''` / `""` в PowerShell и не трогает
  валидные строки

## Что не ловит (честные ограничения)

| Не моделируется | Почему это приемлемо |
|---|---|
| heredoc (`<<EOF`) | агенты генерируют редко, нужен настоящий парсер |
| POSIX `$'...'` (ANSI-C quoting) | редко встречается в генерируемых командах |
| PowerShell `$(...)` внутри `"..."` | вложенная грамматика, сложность не оправдана |
| вложенная подстановка команд | то же |
| **сбалансированная** команда, которая всё равно повиснет | другой класс проблем (например, `Read-Host`) |
| cmd.exe: незакрытая кавычка (`echo "hi`) | cmd.exe печатает её без зависания (вешает только висящий `^`); отсекается консервативно как синтаксический дефект |

Это предохранитель, а не парсер шелла. Он сознательно консервативен в сторону
«не повесить» и не заявляет, что ловит любой возможный зависон. Что он
действительно гарантирует: он не блокирует команду, валидную **в выбранной
грамматике**, и всегда ловит единственный отказ, который молча убивает сессию
агента — незакрытый контекст на конце строки.

## Сделать проверку неизбежной, а не добровольной

CLI, который надо не забыть вызвать, — это та же вероятностная удача. В папке
`hooks/` лежит хук `PreToolUse`, который убирает «не забыть» из уравнения:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "python /path/to/hooks/pre_tool_use_guard.py" }]
    }]
  }
}
```

Код возврата 2 блокирует вызов инструмента и возвращает модели причину. Другие
харнессы — см. [hooks/README.md](hooks/README.md).

## Файлы

| Файл | Назначение |
|---|---|
| [parity_check.py](parity_check.py) | Python-предохранитель — `analyze()` / `verify_quote_parity()`, CLI, `--selftest` |
| [parity_check.js](parity_check.js) | Node-предохранитель — тот же автомат, та же маска heredoc, тот же фикстур кейсов |
| [hooks/pre_tool_use_guard.py](hooks/pre_tool_use_guard.py) | Хук PreToolUse: блокирует зависающие команды до запуска |
| [hooks/README.md](hooks/README.md) | Подключение для Claude Code и других харнессов |
| [tests/test_parity.py](tests/test_parity.py) · [tests/test_parity.js](tests/test_parity.js) | Внешние наборы тестов (46 / 46 проверок на общем фикстуре), без зависимостей |
| [tests/fixtures/cases.jsonl](tests/fixtures/cases.jsonl) | Единственная таблица кейсов, которую читают оба набора — расхождение не пройдёт незамеченным |
| [REQUESTS.md](REQUESTS.md) | Аудит-след: что просили, что приняли и какая проверка это решила |
| [MASTER_PROMPT.md](MASTER_PROMPT.md) | Полный бутстрап сессии для автономного агента |
| [MASTER_PROMPT_LITE.md](MASTER_PROMPT_LITE.md) | Короткий системный промпт (~300 слов) |
| [ARTICLE_RU.md](ARTICLE_RU.md) · [ARTICLE.md](ARTICLE.md) | Статья: притча, подсловная слепота BPE, метод «Архитектор токенов» и почему флагманы всё ещё ломаются о первый метр |
| [WHY_RU.md](WHY_RU.md) | Почему каждый файл сделан именно так — журнал решений |
| [paper/](paper/) | Препринт: исходник LaTeX, английский и русский PDF, архив отправки |
| [protocol/](protocol/) | Протокол аудита: исходник, оба PDF, свой архив отправки |
| [trilogy/](trilogy/) | Трилогия: исходный markdown и скрипт сборки PDF |
| [reproducibility/](reproducibility/) | Проверочный набор — 1 416 проб, 13 скриптов, эталонный вывод и чекеры |
| [archive/](archive/) | Устаревшие промты, оставлены для истории |
| [CITATION.cff](CITATION.cff) · [.zenodo.json](.zenodo.json) | Метаданные цитирования репозитория и релизов GitHub → Zenodo |

## Тесты

```bash
python tests/test_parity.py                       # 46 проверок, 31 грамматический случай
node   tests/test_parity.js                       # 46 проверок, 31 грамматический случай
python tests/test_hook.py                         # 25 проверок
python tests/test_antigravity_hook.py             # 12 проверок
python tools/check_duplicate_blocks.py --selftest # 5 проверок
```

Оба набора для лексера читают один и тот же фикстур —
[tests/fixtures/cases.jsonl](tests/fixtures/cases.jsonl) — поэтому их счётчики
равны по построению: 46 + 46 + 25 + 12 + 5 = **134**, это и есть число на бейдже.
Отдельного файла с числами, которому надо верить, нет: каждый раннер печатает
свой счёт сам, и если счёт перестал совпадать — изменился раннер.

Встроенный `--selftest` (23 кейса в каждой реализации) в сумму не входит: он
проверяет, что предохранитель вообще отвечает, а не таблицу грамматики.

Ни pytest, ни npm install не нужны. Либо код возврата 0, либо сломано.

## Идея

Статья в [ARTICLE_RU.md](ARTICLE_RU.md) отстаивает то, что автор называет
**Топологией неизбежности**: проектировать среду так, чтобы некорректное
состояние было структурно невозможно, вместо того чтобы обучать модель реже в
него попадать. Штрафной RLHF не лечит архитектурную слепоту. Детерминированная
проверка в три строки перед шеллом — лечит.

Инструмент в этом репозитории — минимально возможный экземпляр этой идеи.

## Лицензия

MIT — см. [LICENSE](LICENSE).

*Практик из Kenshi — SkyAngel*
