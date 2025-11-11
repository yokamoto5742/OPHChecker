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
    'DialogSize': {
        'folder_dialog_width': '600',
        'folder_dialog_height': '200',
    },
    'ExcludeItems': {
        'list': '',
    },
    'Paths': {
        'surgery_search_data': '',
        'surgery_schedule': '',
        'template_path': '',
        'output_path': '',
    },
}


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            config.read_file(f)
    except FileNotFoundError:
        print(f"設定ファイルが見つかりません: {CONFIG_PATH}")
        raise
    except PermissionError:
        print(f"設定ファイルを読み取る権限がありません: {CONFIG_PATH}")
        raise
    except configparser.Error as e:
        print(f"設定ファイルの解析中にエラーが発生しました: {e}")
        raise

    # 不足しているセクションにデフォルト値を追加
    _ensure_default_sections(config)
    return config


def save_config(config: configparser.ConfigParser):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except PermissionError:
        print(f"設定ファイルを書き込む権限がありません: {CONFIG_PATH}")
        raise
    except IOError as e:
        print(f"設定ファイルの保存中にエラーが発生しました: {e}")
        raise


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
        'window_width': config.getint('Appearance', 'window_width', fallback=350),
        'window_height': config.getint('Appearance', 'window_height', fallback=350),
    }


def get_dialog_settings(config: configparser.ConfigParser) -> dict:
    return {
        'folder_dialog_width': config.getint('DialogSize', 'folder_dialog_width', fallback=600),
        'folder_dialog_height': config.getint('DialogSize', 'folder_dialog_height', fallback=200),
    }


def get_paths(config: configparser.ConfigParser) -> dict:
    return {
        'surgery_search_data': config.get('Paths', 'surgery_search_data', fallback=''),
        'surgery_schedule': config.get('Paths', 'surgery_schedule', fallback=''),
        'template_path': config.get('Paths', 'template_path', fallback=''),
        'output_path': config.get('Paths', 'output_path', fallback=''),
    }


def get_exclude_items(config: configparser.ConfigParser) -> list:
    items_str = config.get('ExcludeItems', 'list', fallback='')
    return [item.strip() for item in items_str.split(',') if item.strip()]
