import configparser
import os
import sys


def get_config_path() -> str:
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた実行ファイルの場合
        base_path = sys._MEIPASS  # type: ignore
    else:
        # 通常のPythonスクリプトとして実行される場合
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, 'config.ini')


CONFIG_PATH = get_config_path()

# デフォルト設定値
DEFAULT_CONFIG = {
    'Appearance': {
        'font_size': '11',
        'window_width': '350',
        'window_height': '350',
    },
    'ExcludeItems': {
        'exclusion_line_keywords': '★,霰粒腫,術式未定,先天性鼻涙管閉塞開放術',
        'surgery_strings_to_remove': '(クラレオントーリック),(クラレオンパンオプティクス),(クラレオンパンオプティクストーリック),(ビビティ),(ビビティトーリック),(アイハンストーリックⅡ),(トーリック),(inject)',
    },
    'Paths': {
        'surgery_search_data': '',
        'processed_surgery_search_data': '',
        'surgery_schedule': '',
        'processed_surgery_schedule': '',
        'comparison_result': '',
        'template_path': '',
        'output_path': '',
        'excludeitems_file': '',
        'replacements_file': '',
    },
    'Replacements': {
        'anesthesia_replacements': '球後麻酔:局所,局所麻酔:局所,点眼麻酔:局所,全身麻酔:全身,結膜下:局所',
        'surgeon_replacements': '橋本義弘:橋本,植田芳樹:植田,増子杏:増子,田中伸弥:田中,渡辺裕士:渡辺,鈴木貴文:鈴木',
        'inpatient_replacements': 'あやめ:入院,わかば:入院,さくら:入院,外来:外来',
    },
}


def _load_settings_file(config: configparser.ConfigParser, path_key: str, section: str) -> configparser.ConfigParser:
    """
    txtを読み込み、不足キーをDEFAULT_CONFIGで補う
    ファイルが存在しない場合はデフォルト値を返す（存在するのに読めない場合は例外）
    """
    settings = configparser.ConfigParser()
    file_path = config.get('Paths', path_key, fallback='')

    if file_path and os.path.exists(file_path):
        with open(file_path, encoding='utf-8') as settings_file:
            settings.read_file(settings_file)

    if not settings.has_section(section):
        settings.add_section(section)
    for key, default_value in DEFAULT_CONFIG[section].items():
        if not settings.has_option(section, key):
            settings.set(section, key, default_value)

    return settings


def _save_settings_file(
        config: configparser.ConfigParser, path_key: str, section: str, values: dict[str, str]
) -> None:
    """txtの指定セクションの値を書き換えて保存"""
    settings = _load_settings_file(config, path_key, section)
    file_path = config.get('Paths', path_key, fallback='')
    if not file_path:
        raise ValueError(f"{path_key} のパスが設定されていません")

    for key, value in values.items():
        settings.set(section, key, value)
    with open(file_path, 'w', encoding='utf-8') as settings_file:
        settings.write(settings_file)


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    with open(CONFIG_PATH, encoding='utf-8') as f:
        config.read_file(f)

    # 不足しているセクションにデフォルト値を追加
    _ensure_default_sections(config)
    return config


def save_config(config: configparser.ConfigParser):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile:
        config.write(configfile)


def _ensure_default_sections(config: configparser.ConfigParser) -> None:
    for section, options in DEFAULT_CONFIG.items():
        if not config.has_section(section):
            config.add_section(section)
        for key, default_value in options.items():
            if not config.has_option(section, key):
                config.set(section, key, default_value)


def get_appearance_settings(config: configparser.ConfigParser) -> dict:
    return {
        'font_size': config.getint('Appearance', 'font_size', fallback=11),
        'log_font_size': config.getint('Appearance', 'log_font_size', fallback=9),
        'window_width': config.getint('Appearance', 'window_width', fallback=350),
        'window_height': config.getint('Appearance', 'window_height', fallback=350),
    }


def get_paths(config: configparser.ConfigParser) -> dict:
    return {
        'input_path': config.get('Paths', 'input_path', fallback=''),
        'surgery_search_data': config.get('Paths', 'surgery_search_data', fallback=''),
        'processed_surgery_search_data': config.get('Paths', 'processed_surgery_search_data', fallback=''),
        'surgery_schedule': config.get('Paths', 'surgery_schedule', fallback=''),
        'processed_surgery_schedule': config.get('Paths', 'processed_surgery_schedule', fallback=''),
        'comparison_result': config.get('Paths', 'comparison_result', fallback=''),
        'template_path': config.get('Paths', 'template_path', fallback=''),
        'output_path': config.get('Paths', 'output_path', fallback=''),
    }


def get_exclude_items(config: configparser.ConfigParser) -> dict[str, list[str]]:
    """除外設定（行除外キーワード・手術文字列削除リスト）をキー名→リストで取得"""
    settings = _load_settings_file(config, 'excludeitems_file', 'ExcludeItems')
    return {
        key: [item.strip() for item in settings.get('ExcludeItems', key).split(',') if item.strip()]
        for key in DEFAULT_CONFIG['ExcludeItems']
    }


def save_exclude_items(config: configparser.ConfigParser, exclude_items: dict[str, list[str]]) -> None:
    """除外設定をまとめて保存"""
    _save_settings_file(config, 'excludeitems_file', 'ExcludeItems', {
        key: ','.join(item.strip() for item in items if item.strip())
        for key, items in exclude_items.items()
    })


def _parse_replacement_pairs(replacement_str: str) -> dict[str, str]:
    """'置換前:置換後,...' 形式の文字列を辞書に変換"""
    replacement_dict = {}
    for pair in replacement_str.split(','):
        pair = pair.strip()
        if ':' in pair:
            source, target = pair.split(':', 1)
            replacement_dict[source.strip()] = target.strip()

    return replacement_dict


def get_replacements(config: configparser.ConfigParser) -> dict[str, dict[str, str]]:
    """置換設定（麻酔・医師・入外）をキー名→置換辞書で取得"""
    settings = _load_settings_file(config, 'replacements_file', 'Replacements')
    return {
        key: _parse_replacement_pairs(settings.get('Replacements', key))
        for key in DEFAULT_CONFIG['Replacements']
    }


def save_replacements(config: configparser.ConfigParser, replacements: dict[str, dict[str, str]]) -> None:
    """置換設定をまとめて保存"""
    _save_settings_file(config, 'replacements_file', 'Replacements', {
        key: ','.join(f"{source}:{target}" for source, target in replacement_dict.items())
        for key, replacement_dict in replacements.items()
    })
