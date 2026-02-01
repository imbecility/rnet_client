# rnet_client

Обёртка над библиотекой [rnet](https://github.com/0x676e67/rnet) для создания [самого быстрого](https://github.com/0x676e67/rnet/blob/main/python/benchmark/benchmark_results.csv) HTTP-клиента в Python с расширенными настройками: случайная эмуляция браузера, кастомные редиректы и оптимальные тайм-ауты. Возвращает готовый клиент с низкоуровневой эмуляцией, с настраиваемыми возможностями TLS, JA3/JA4 и HTTP/2, на базе [wreq](https://github.com/0x676e67/wreq).

## Установка

```bash
uv add rnet-client
```

Требуется RC-релиз rnet: `uv add --upgrade --prerelease allow rnet`

## Быстрый старт

```python
from rnet_client import get_rnet_client

# Создание клиента с настройками по умолчанию
client = get_rnet_client()

# Асинхронный запрос
async def main():
    response = await client.get("https://httpbin.org/get")
    print(await response.text())
```

## API

### `get_rnet_client()`

Фабрика для создания сконфигурированного `rnet.Client`.

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `browser` | `Browsers \| list[str] \| None` | `None` | Семейство браузеров для эмуляции |
| `max_redirects` | `int` | `36` | Максимальное количество редиректов |
| `ignore_in_redirects` | `list[str] \| None` | `None` | Подстроки URL для прерывания редиректов |
| `connect_timeout` | `int` | `15` | Тайм-аут соединения (сек) |
| `read_timeout` | `int` | `20` | Тайм-аут чтения (сек) |
| `pool_idle_timeout` | `int` | `90` | Время простоя соединения в пуле (сек) |
| `pool_max_idle_per_host` | `int` | `15` | Макс. простаивающих соединений на хост |
| `headers` | `dict[str, str] \| None` | `None` | Дополнительные заголовки |
| `referer` | `bool` | `True` | Автоматический заголовок `Referer` |
| `gzip` | `bool` | `True` | Поддержка gzip |
| `brotli` | `bool` | `True` | Поддержка brotli |
| `deflate` | `bool` | `True` | Поддержка deflate |
| `zstd` | `bool` | `True` | Поддержка zstd |

### `Browsers`

Доступные семейства браузеров для эмуляции:

- `'Chrome'`
- `'Edge'`
- `'Firefox'`
- `'SafariDesktop'`
- `'iOS'`

## Примеры

### Эмуляция конкретного браузера

```python
# Только Chrome
client = get_rnet_client(browser='Chrome')

# Chrome или Firefox
client = get_rnet_client(browser=['Chrome', 'Firefox'])
```

### Кастомные редиректы

```python
# Прерывать редиректы при переходе на определённые домены
client = get_rnet_client(
    max_redirects=10,
    ignore_in_redirects=['login.example.com', 'auth.']
)
```

### Настройка тайм-аутов

```python
client = get_rnet_client(
    connect_timeout=30,
    read_timeout=60,
    pool_idle_timeout=120
)
```

### Дополнительные заголовки

```python
client = get_rnet_client(
    headers={
        'X-Custom-Header': 'value',
        'Accept-Language': 'ru-RU,ru;q=0.9'
    }
)
```

