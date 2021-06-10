# Project MicroChat

## Установка

Перед выполнением следующих действий склонируйте репозиторий и перейдите в папку с исходниками проекта.

### Установка на Linux

``` bash
python3 -m venv ./.venv
./.venv/Scripts/activate
pip3 install -r requirements.txt
```

### Установка на Windows

``` batch
python -m venv ./.venv
"./.venv/Scripts/activate"
pip install -r requirements.txt
```

## Запуск

Перед выполнением следующих действий перейдите в папку проекта.

Внимание, для работы проекта требуется установленная СУБД PostgreSQL с созданной в ней БД.
Не забудьте внести соответствующую информацию в файл config.py

### Запуск на Linux

``` bash
./.venv/Scripts/activate
python3 run.py
```

### Запуск на Windows

``` batch
"./.venv/Scripts/activate"
python run.py
```
