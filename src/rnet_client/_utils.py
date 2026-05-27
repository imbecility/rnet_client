from collections import defaultdict
from random import choice
from re import compile
from typing import TypedDict, get_args, Literal

try:
    from wreq import Emulation, Profile, Platform
    from wreq.redirect import Attempt, Action, Policy
except (ImportError, ModuleNotFoundError):
    raise ImportError('ВАЖНО установить: `uv add --upgrade wreq`')

VERSION_PATTERN = compile(r"(\d+)(?:_(\d+))?(?:_(\d+))?")

Browsers = Literal['Chrome', 'Edge', 'Firefox', 'SafariDesktop', 'iOS']


class _EmulationMeta(TypedDict):
    member: Profile
    name: str
    category: str
    version: tuple[int, ...]


class _EmulationRandomizer:
    """
    утилита для случайного выбора профиля эмуляции из библиотеки wreq.

    класс анализирует доступные в `wreq.Profile` профили, группирует их
    по семействам (браузер/платформа) и версиям, а затем позволяет выбрать
    случайный профиль из числа последних версий для создания экземпляра `wreq.Client`.

    Attributes:
        selected_os (Platform | str): выбранная платформа после генерации опции.
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
        self.selected_os: Platform | str = 'Unknown'
        self.selected_browser: str = 'Unknown'

    def _parse_and_group(self):
        """
        анализирует, сортирует и группирует все доступные эмуляции по категориям.

        метод извлекает версии из имён профилей, определяет их категорию
        (например, 'Chrome', 'iOS') и сохраняет отсортированные по версии
        результаты во внутреннем атрибуте `_grouped_emulations`.
        """
        temp_items: list[_EmulationMeta] = []

        # использование dir() обеспечивает совместимость как со стандартными Enum,
        # так и с нативными классами PyO3 на уровне среды выполнения.
        for name in dir(Profile):
            if name.startswith("_"):
                continue

            member = getattr(Profile, name)
            if callable(member):
                continue

            category = self._get_category(name)
            if category == 'Unknown':
                continue

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
        if name.startswith('Chrome'): return 'Chrome'
        if name.startswith('Edge'): return 'Edge'
        if name.startswith('Firefox'): return 'Firefox'
        if name.startswith('Opera'): return 'Opera'
        if 'OkHttp' in name: return 'AndroidNative'
        if 'Android' in name: return 'AndroidBrowser'
        if 'Ios' in name or 'IPad' in name: return 'iOS'
        if name.startswith('Safari'): return 'SafariDesktop'
        return 'Unknown'

    @staticmethod
    def _get_compatible_platform(category: str) -> Platform:
        """
        возвращает случайную совместимую операционную систему для указанной категории.

        Args:
            category (str): категория браузера или платформы (например, 'Chrome', 'iOS').

        Returns:
            EmulationOS: случайный совместимый член перечисления `EmulationOS`.
        """
        mapping = {
            'Chrome': [Platform.Windows, Platform.MacOS, Platform.Linux],
            'Edge': [Platform.Windows, Platform.MacOS],
            'Firefox': [Platform.Windows, Platform.MacOS, Platform.Linux],
            'Opera': [Platform.Windows, Platform.MacOS],
            'SafariDesktop': [Platform.MacOS],
            'iOS': [Platform.IOS],
            'AndroidNative': [Platform.Android],
            'AndroidBrowser': [Platform.Android],
        }
        allowed_platforms = mapping.get(category, [Platform.Windows])
        return choice(allowed_platforms)

    def _pick_params(self, families: list[str] | None, latest_n: int) -> tuple[Profile, Platform]:
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

        profile = chosen_item['member']
        platform = self._get_compatible_platform(chosen_family)

        self.selected_os, self.selected_browser = platform, chosen_item['name']
        return profile, platform

    def get_option(self, families: list[str] | None = None, latest_n: int = 5) -> Emulation:
        """
        генерирует и возвращает готовый объект `Emulation` со случайными параметрами.

        основной публичный метод для получения сконфигурированного объекта,
        готового для передачи в конструктор `wreq.Client`.

        Args:
            families (list[str] | None, optional): список семейств браузеров для выбора.
                по умолчанию `None`, что приводит к использованию стандартного набора
                ('Chrome', 'Edge', 'Firefox', 'SafariDesktop', 'iOS').
            latest_n (int, optional): количество последних версий в каждом семействе
                для случайного выбора. по умолчанию 5.

        Returns:
            Emulation: сконфигурированный объект с параметрами эмуляции.
        """
        profile, platform = self._pick_params(families, latest_n)
        return Emulation(
            profile=profile,
            platform=platform
        )


_wreq_randomizer = _EmulationRandomizer()


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
