# Project MicroChat

## Установка

Перед выполнением следующих действий склонируйте репозиторий и перейдите в папку с исходниками проекта.

### Linux

``` bash
python3 -m venv ./.venv
./.venv/Scripts/activate
pip3 install -r requirements.txt
```

### Windows

``` batch
python -m venv ./.venv
"./.venv/Scripts/activate"
pip install -r requirements.txt
```

## Запуск

Перед выполнением следующих действий склонируйте репозиторий и перейдите в папку с исходниками проекта.

Внимание, для работы проекта требуется установленная СУБД PostgreSQL с созданной в ней БД.
Не забудьте внести соответствующую информацию в файл config.py

### Linux

``` bash
./.venv/Scripts/activate
python3 run.py
```

### Windows

``` batch
"./.venv/Scripts/activate"
python run.py
```
