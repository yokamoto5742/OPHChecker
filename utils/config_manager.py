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


def _get_exclude_items_file_path(config: configparser.ConfigParser) -> str:
    """excludeitems.txt のパスを取得"""
    return config.get('Paths', 'excludeitems_file', fallback='')


def _get_replacements_file_path(config: configparser.ConfigParser) -> str:
    """replacements.txt のパスを取得"""
    return config.get('Paths', 'replacements_file', fallback='')


def _load_exclude_items_config(config: configparser.ConfigParser) -> configparser.ConfigParser:
    """
    excludeitems.txt から除外項目設定を読み込む
    ファイルが存在しない場合はデフォルト値を返す
    """
    exclude_config = configparser.ConfigParser()
    file_path = _get_exclude_items_file_path(config)
    
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, encoding='utf-8') as f:
                exclude_config.read_file(f)
        except Exception as e:
            print(f"除外項目ファイルの読み込みエラー: {e}")
    
    # デフォルト値を設定
    if not exclude_config.has_section('ExcludeItems'):
        exclude_config.add_section('ExcludeItems')
    if not exclude_config.has_option('ExcludeItems', 'exclusion_line_keywords'):
        exclude_config.set('ExcludeItems', 'exclusion_line_keywords', 
                          DEFAULT_CONFIG['ExcludeItems']['exclusion_line_keywords'])
    if not exclude_config.has_option('ExcludeItems', 'surgery_strings_to_remove'):
        exclude_config.set('ExcludeItems', 'surgery_strings_to_remove',
                          DEFAULT_CONFIG['ExcludeItems']['surgery_strings_to_remove'])
    
    return exclude_config


def _load_replacements_config(config: configparser.ConfigParser) -> configparser.ConfigParser:
    """
    replacements.txt から置換項目設定を読み込む
    ファイルが存在しない場合はデフォルト値を返す
    """
    replacements_config = configparser.ConfigParser()
    file_path = _get_replacements_file_path(config)
    
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, encoding='utf-8') as f:
                replacements_config.read_file(f)
        except Exception as e:
            print(f"置換項目ファイルの読み込みエラー: {e}")
    
    # デフォルト値を設定
    if not replacements_config.has_section('Replacements'):
        replacements_config.add_section('Replacements')
    for key in ['anesthesia_replacements', 'surgeon_replacements', 'inpatient_replacements']:
        if not replacements_config.has_option('Replacements', key):
            replacements_config.set('Replacements', key, DEFAULT_CONFIG['Replacements'][key])
    
    return replacements_config


def _save_exclude_items_config(config: configparser.ConfigParser, exclude_config: configparser.ConfigParser) -> None:
    """excludeitems.txt に除外項目設定を保存"""
    file_path = _get_exclude_items_file_path(config)
    if not file_path:
        raise ValueError("excludeitems_file のパスが設定されていません")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            exclude_config.write(f)
    except Exception as e:
        print(f"除外項目ファイルの保存エラー: {e}")
        raise


def _save_replacements_config(config: configparser.ConfigParser, replacements_config: configparser.ConfigParser) -> None:
    """replacements.txt に置換項目設定を保存"""
    file_path = _get_replacements_file_path(config)
    if not file_path:
        raise ValueError("replacements_file のパスが設定されていません")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            replacements_config.write(f)
    except Exception as e:
        print(f"置換項目ファイルの保存エラー: {e}")
        raise


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
        'log_font_size': config.getint('Appearance', 'log_font_size', fallback=9),
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
        'input_path': config.get('Paths', 'input_path', fallback=''),
        'surgery_search_data': config.get('Paths', 'surgery_search_data', fallback=''),
        'processed_surgery_search_data': config.get('Paths', 'processed_surgery_search_data', fallback=''),
        'surgery_schedule': config.get('Paths', 'surgery_schedule', fallback=''),
        'processed_surgery_schedule': config.get('Paths', 'processed_surgery_schedule', fallback=''),
        'comparison_result': config.get('Paths', 'comparison_result', fallback=''),
        'template_path': config.get('Paths', 'template_path', fallback=''),
        'output_path': config.get('Paths', 'output_path', fallback=''),
    }


def get_exclude_items(config: configparser.ConfigParser) -> list:
    items_str = config.get('ExcludeItems', 'list', fallback='')
    return [item.strip() for item in items_str.split(',') if item.strip()]


def get_exclusion_line_keywords(config: configparser.ConfigParser) -> list:
    exclude_config = _load_exclude_items_config(config)
    keywords_str = exclude_config.get('ExcludeItems', 'exclusion_line_keywords', fallback='')
    return [keyword.strip() for keyword in keywords_str.split(',') if keyword.strip()]


def get_surgery_strings_to_remove(config: configparser.ConfigParser) -> list:
    exclude_config = _load_exclude_items_config(config)
    strings_str = exclude_config.get('ExcludeItems', 'surgery_strings_to_remove', fallback='')
    return [string.strip() for string in strings_str.split(',') if string.strip()]


def get_replacement_dict(config: configparser.ConfigParser, section: str, key: str) -> dict:
    """
    設定ファイルから置換用の辞書を取得

    Args:
        config: configparserオブジェクト
        section: セクション名
        key: キー名

    Returns:
        置換辞書
    """
    replacements_config = _load_replacements_config(config)
    replacement_str = replacements_config.get(section, key, fallback='')
    if not replacement_str:
        return {}

    replacement_dict = {}
    for pair in replacement_str.split(','):
        pair = pair.strip()
        if ':' in pair:
            source, target = pair.split(':', 1)
            replacement_dict[source.strip()] = target.strip()

    return replacement_dict


def save_replacement_dict(config: configparser.ConfigParser, section: str, key: str, replacement_dict: dict[str, str]) -> None:
    """
    置換辞書を設定ファイルに保存

    Args:
        config: configparserオブジェクト
        section: セクション名
        key: キー名
        replacement_dict: 置換辞書
    """
    replacements_config = _load_replacements_config(config)
    pairs = [f"{source}:{target}" for source, target in replacement_dict.items()]
    replacement_str = ','.join(pairs)
    replacements_config.set(section, key, replacement_str)
    _save_replacements_config(config, replacements_config)


def save_exclusion_line_keywords(config: configparser.ConfigParser, keywords: list[str]) -> None:
    """
    行除外キーワードを保存

    Args:
        config: configparserオブジェクト
        keywords: キーワードリスト
    """
    exclude_config = _load_exclude_items_config(config)
    keywords_str = ','.join(keyword.strip() for keyword in keywords if keyword.strip())
    exclude_config.set('ExcludeItems', 'exclusion_line_keywords', keywords_str)
    _save_exclude_items_config(config, exclude_config)


def save_surgery_strings_to_remove(config: configparser.ConfigParser, strings: list[str]) -> None:
    """
    手術文字列削除リストを保存

    Args:
        config: configparserオブジェクト
        strings: 削除文字列リスト
    """
    exclude_config = _load_exclude_items_config(config)
    strings_str = ','.join(string.strip() for string in strings if string.strip())
    exclude_config.set('ExcludeItems', 'surgery_strings_to_remove', strings_str)
    _save_exclude_items_config(config, exclude_config)
