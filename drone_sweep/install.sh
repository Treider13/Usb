#!/bin/sh
# Установка Стрелы в локальное окружение этого каталога.
set -eu
cd "$(dirname "$0")"
python3 -m venv .venv || {
  echo "Не удалось создать окружение. Установите пакет python3-venv и запустите установку снова."
  exit 1
}
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install .
echo "Стрела установлена."
echo "Запуск меню: $PWD/.venv/bin/strela"
echo "Страница:    $PWD/.venv/bin/strela serve --port 8765"
