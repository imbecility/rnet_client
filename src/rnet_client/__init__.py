from datetime import timedelta

try:
    from rnet import Client
except (ImportError, ModuleNotFoundError):
    raise ImportError('ВАЖНО ставить RC-релиз: `uv add --upgrade --prerelease allow rnet`')

from _utils import _custom_redirects, _normalize_browser_param, _rnet_randomizer, Browsers


def get_rnet_client(
        browser: Browsers | list[str] | None = None,
        max_redirects=36,
        ignore_in_redirects: list[str] | None = None,
        connect_timeout: int = 15,
        read_timeout: int = 20,
        pool_idle_timeout: int = 90,
        pool_max_idle_per_host: int = 15,
        headers: dict[str, str] | None = None,
        referer: bool = True,
        gzip: bool = True,
        brotli: bool = True,
        deflate: bool = True,
        zstd: bool = True,
) -> Client:
    """
    создает и возвращает экземпляр `rnet.Client` с расширенными настройками.

    функция-фабрика для создания экземпляра `rnet.Client` с предустановленными
    параметрами, включая случайную эмуляцию браузера из последних версий,
    кастомную политику обработки редиректов и оптимальные тайм-ауты.

    Args:
       browser (Literal[...] | list[str] | None, optional): семейство браузеров для эмуляции.
           можно указать одно (`'Chrome'`) или несколько в списке. если `None`,
           выбирается из всех доступных. по умолчанию `None`.
       max_redirects (int, optional): максимальное количество разрешенных редиректов.
           по умолчанию 36.
       ignore_in_redirects (list[str] | None, optional): список подстрок в url,
           при наличии которых цепочка редиректов прерывается. по умолчанию `None`.
       connect_timeout (int, optional): тайм-аут на установку соединения в секундах.
           по умолчанию 15.
       read_timeout (int, optional): тайм-аут на чтение ответа в секундах.
           по умолчанию 20.
       pool_idle_timeout (int, optional): время простоя соединения в пуле в секундах.
           по умолчанию 90.
       pool_max_idle_per_host (int, optional): максимальное количество простаивающих
           соединений на хост. по умолчанию 15.
       headers (dict[str, str] | None, optional): дополнительные заголовки,
           применяемые ко всем запросам. по умолчанию `None`.
       referer (bool, optional): автоматическое добавление заголовка `Referer`.
           по умолчанию `True`.
       gzip (bool, optional): поддержка сжатия gzip. по умолчанию `True`.
       brotli (bool, optional): поддержка сжатия brotli. по умолчанию `True`.
       deflate (bool, optional): поддержка сжатия deflate. по умолчанию `True`.
       zstd (bool, optional): поддержка сжатия zstd. по умолчанию `True`.

    Returns:
       Client: сконфигурированный экземпляр клиента `rnet.Client`, готовый к использованию.
    """
    kwargs = dict(
        emulation=_rnet_randomizer.get_option(families=_normalize_browser_param(browser), latest_n=5),
        redirect=_custom_redirects(max_redirects=max_redirects, ignore_in_redirects=ignore_in_redirects),
        cookie_store=True,
        tcp_reuse_address=True,
        https_only=False,
        verify=False,
        connect_timeout=timedelta(seconds=connect_timeout),
        read_timeout=timedelta(seconds=read_timeout),
        pool_idle_timeout=timedelta(seconds=pool_idle_timeout),
        pool_max_idle_per_host=pool_max_idle_per_host,
        headers=headers,
        referer=referer,
        gzip=gzip,
        brotli=brotli,
        deflate=deflate,
        zstd=zstd,
    )
    return Client(**kwargs)


__all__ = [
    'Browsers',
    'get_rnet_client',
]
