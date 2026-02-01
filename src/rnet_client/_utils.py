from collections import defaultdict
from random import choice
from re import compile
from typing import TypedDict, get_args, Literal

try:
    from rnet import Emulation, EmulationOption, EmulationOS
    from rnet.redirect import Attempt, Action, Policy
except (ImportError, ModuleNotFoundError):
    raise ImportError('ВАЖНО ставить RC-релиз: `uv add --upgrade --prerelease allow rnet`')

VERSION_PATTERN = compile(r"(\d+)(?:_(\d+))?(?:_(\d+))?")

Browsers = Literal['Chrome', 'Edge', 'Firefox', 'SafariDesktop', 'iOS']


class _EmulationMeta(TypedDict):
    member: Emulation
    name: str
    category: str
    version: tuple[int, ...]


class _EmulationRandomizer:
    """
    утилита для случайного выбора профиля эмуляции из библиотеки rnet.

    класс анализирует доступные в `rnet.Emulation` профили, группирует их
    по семействам (браузер/платформа) и версиям, а затем позволяет выбрать
    случайный профиль из числа последних версий для создания экземпляра `rnet.Client`.

    Attributes:
        selected_os (str): название выбранной операционной системы после генерации опции.
        selected_browser (str): название выбранного профиля браузера после генерации опции.
    """

    def __init__(self):
        """
        инициализирует экземпляр EmulationRandomizer.

        выполняет парсинг и группировку доступных профилей эмуляции,
        а также инициализирует атрибуты для хранения последнего выбора.
        """
        self._grouped_emulations: dict[str, list[_EmulationMeta]] = defaultdict(list)
        self._parse_and_group()
        self.selected_os: str = 'Unknown'
        self.selected_browser: str = 'Unknown'

    @staticmethod
    def _get_all_emulations():
        """
        извлекает все доступные эмуляции из класса `rnet.Emulation`.

        Returns:
            list[tuple[str, Emulation]]: список кортежей, где каждый содержит
            имя атрибута и соответствующий ему объект эмуляции.
        """
        emulations = []
        for attr_name in dir(Emulation):
            if attr_name.startswith("_"): continue
            val = getattr(Emulation, attr_name)
            emulations.append((attr_name, val))
        return emulations

    def _parse_and_group(self):
        """
        анализирует, сортирует и группирует все доступные эмуляции по категориям.

        метод извлекает версии из имён профилей, определяет их категорию
        (например, 'Chrome', 'iOS') и сохраняет отсортированные по версии
        результаты во внутреннем атрибуте `_grouped_emulations`.
        """
        temp_items: list[_EmulationMeta] = []

        all_members = self._get_all_emulations()

        for name, member in all_members:
            # фильтрация методов/служебных полей, если они попали
            if not isinstance(name, str): continue

            category = self._get_category(name)
            if category == 'Unknown': continue

            v_match = VERSION_PATTERN.search(name)
            version_tuple = tuple(map(int, v_match.groups(default='0'))) if v_match else (0,)

            temp_items.append({
                'member': member,
                'name': name,
                'category': category,
                'version': version_tuple
            })

        sorted_items = sorted(temp_items, key=lambda x: x['version'])

        for item in sorted_items:
            self._grouped_emulations[item['category']].append(item)

    @staticmethod
    def _get_category(name: str) -> str:
        """
        определяет категорию эмуляции по её имени.

        Args:
            name (str): имя профиля эмуляции (например, 'Chrome_125').

        Returns:
            str: строка с названием категории ('Chrome', 'iOS' и т.д.)
            или 'Unknown', если категория не определена.
        """
        if 'OkHttp' in name: return 'AndroidNative'
        if 'Android' in name: return 'AndroidBrowser'
        if 'Ios' in name or 'IPad' in name: return 'iOS'
        if name.startswith('Safari'): return 'SafariDesktop'
        if name.startswith('Chrome'): return 'Chrome'
        if name.startswith('Edge'): return 'Edge'
        if name.startswith('Firefox'): return 'Firefox'
        if name.startswith('Opera'): return 'Opera'
        return 'Unknown'

    @staticmethod
    def _get_compatible_os(category: str) -> EmulationOS:
        """
        возвращает случайную совместимую операционную систему для указанной категории.

        Args:
            category (str): категория браузера или платформы (например, 'Chrome', 'iOS').

        Returns:
            EmulationOS: случайный совместимый член перечисления `EmulationOS`.
        """
        mapping = {
            'Chrome': [EmulationOS.Windows, EmulationOS.MacOS, EmulationOS.Linux],
            'Edge': [EmulationOS.Windows, EmulationOS.MacOS],
            'Firefox': [EmulationOS.Windows, EmulationOS.MacOS, EmulationOS.Linux],
            'Opera': [EmulationOS.Windows, EmulationOS.MacOS],
            'SafariDesktop': [EmulationOS.MacOS],
            'iOS': [EmulationOS.IOS],
            'AndroidNative': [EmulationOS.Android],
            'AndroidBrowser': [EmulationOS.Android],
        }
        allowed_os = mapping.get(category, [EmulationOS.Windows])
        return choice(allowed_os)

    def _pick_params(self, families, latest_n) -> tuple[Emulation, EmulationOS]:
        """
        выбирает случайный профиль эмуляции и совместимую с ним ос.

        метод выбирает семейство браузеров, затем один из `latest_n` последних
        профилей в этом семействе и подбирает для него совместимую ос.
        результат выбора сохраняется в атрибутах `selected_os` и `selected_browser`.

        Args:
            families (list[str] | None): список семейств браузеров для выбора.
                если `None`, используется список по умолчанию.
            latest_n (int): количество последних версий в семействе,
                из которых будет сделан случайный выбор.

        Returns:
            tuple[Emulation, EmulationOS]: кортеж, содержащий выбранный
            объект эмуляции и совместимую ос.
        """
        if not families:
            families = ['Chrome', 'Edge', 'Firefox', 'SafariDesktop', 'iOS']
            families = [f for f in families if f in self._grouped_emulations]

        chosen_family = choice(families)
        available_items = self._grouped_emulations.get(chosen_family, [])

        if not available_items:
            available_items = self._grouped_emulations.get('Chrome', [])
            chosen_family = 'Chrome'

        candidates = available_items[-latest_n:]
        chosen_item = choice(candidates)

        emulation_ver = chosen_item['member']  # сам объект Emulation
        emulation_os = self._get_compatible_os(chosen_family)

        self.selected_os, self.selected_browser = emulation_os, chosen_item['name']
        return emulation_ver, emulation_os

    def get_option(self, families: list[str] | None = None, latest_n: int = 5) -> EmulationOption:
        """
        генерирует и возвращает готовый объект `EmulationOption` со случайными параметрами.

        основной публичный метод для получения сконфигурированного объекта,
        готового для передачи в конструктор `rnet.Client`.

        Args:
            families (list[str] | None, optional): список семейств браузеров для выбора.
                по умолчанию `None`, что приводит к использованию стандартного набора
                ('Chrome', 'Edge', 'Firefox', 'SafariDesktop', 'iOS').
            latest_n (int, optional): количество последних версий в каждом семействе
                для случайного выбора. по умолчанию 5.

        Returns:
            EmulationOption: сконфигурированный объект с параметрами эмуляции.
        """
        emulation_ver, emulation_os = self._pick_params(families, latest_n)
        return EmulationOption(
            emulation=emulation_ver,
            emulation_os=emulation_os
        )


_rnet_randomizer = _EmulationRandomizer()


def _normalize_browser_param(browser):
    if browser is None:
        return None
    valid_browsers = get_args(Browsers)
    if isinstance(browser, str):
        browser = browser.strip()
        if not browser:
            return None
        if browser not in valid_browsers:
            return None
        return browser
    if isinstance(browser, list):
        if not browser:
            return None
        normalized = []
        for item in browser:
            if not isinstance(item, str):
                return None
            item = item.strip()
            if not item or item not in valid_browsers:
                continue
            normalized.append(item)
        return normalized or None
    raise None


def _make_custom_redirects_policy(
        max_redirects: int = 36,
        ignore_in_redirects: list[str] | None = None
):
    def policy(attempt: Attempt) -> Action:
        if ignore_in_redirects and any(ignored in attempt.next for ignored in ignore_in_redirects):
            return attempt.stop()
        if len(attempt.previous) > max_redirects:
            return attempt.error(f"Too many redirects (>{max_redirects})")
        return attempt.follow()

    return policy


def _custom_redirects(
        max_redirects: int = 36,
        ignore_in_redirects: list[str] | None = None
):
    return Policy.custom(
        _make_custom_redirects_policy(
            max_redirects=max_redirects,
            ignore_in_redirects=ignore_in_redirects
        )
    )
