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
export STRELA_DATA="$PWD/strela-data"
.venv/bin/strela setup --lite
echo "Стрела установлена."
echo "Данные:      $STRELA_DATA (словари ELRS, без rockyou — режим --lite)"
echo "Полный rockyou: STRELA_DATA=$STRELA_DATA $PWD/.venv/bin/strela setup --force"
echo "Запуск меню: $PWD/.venv/bin/strela"
echo "Страница:    STRELA_DATA=$STRELA_DATA $PWD/.venv/bin/strela serve --port 8765"
