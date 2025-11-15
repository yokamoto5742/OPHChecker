import configparser
import os
import tempfile
from unittest.mock import patch

import pytest

from utils.config_manager import (
    get_appearance_settings,
    get_dialog_settings,
    get_exclusion_line_keywords,
    get_paths,
    get_replacement_dict,
    get_surgery_strings_to_remove,
    load_config,
    save_config,
    save_exclusion_line_keywords,
    save_replacement_dict,
    save_surgery_strings_to_remove,
)


@pytest.fixture
def temp_config_file():
    """一時的な設定ファイルを作成"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini', encoding='utf-8') as f:
        f.write("""[Appearance]
font_size = 11
log_font_size = 9
window_width = 350
window_height = 350

[DialogSize]
folder_dialog_width = 600
folder_dialog_height = 200

[ExcludeItems]
list =
exclusion_line_keywords = ★,霰粒腫,術式未定
surgery_strings_to_remove = (トーリック),(inject)

[Paths]
input_path = C:\\test\\input
surgery_search_data = C:\\test\\search.csv
processed_surgery_search_data = C:\\test\\processed_search.csv
surgery_schedule = C:\\test\\schedule.xlsx
processed_surgery_schedule = C:\\test\\processed_schedule.csv
comparison_result = C:\\test\\comparison.csv
template_path = C:\\test\\template.xlsx
output_path = C:\\test\\output

[Replacements]
anesthesia_replacements = 球後麻酔:局所,点眼麻酔:局所
surgeon_replacements = 橋本義弘:橋本,植田芳樹:植田
inpatient_replacements = あやめ:入院,外来:外来
""")
        temp_path = f.name

    yield temp_path

    # クリーンアップ
    try:
        os.unlink(temp_path)
    except:
        pass


def test_load_config_success(temp_config_file):
    """設定ファイルの読み込みが成功する"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        assert config is not None
        assert config.has_section('Appearance')
        assert config.has_section('Paths')


def test_load_config_file_not_found():
    """存在しない設定ファイルでエラーが発生する"""
    with patch('utils.config_manager.CONFIG_PATH', 'C:\\nonexistent\\config.ini'):
        with pytest.raises(FileNotFoundError):
            load_config()


def test_save_config_success(temp_config_file):
    """設定ファイルの保存が成功する"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        config.set('Appearance', 'font_size', '12')
        save_config(config)

        # 再読み込みして確認
        config2 = load_config()
        assert config2.get('Appearance', 'font_size') == '12'


def test_get_appearance_settings(temp_config_file):
    """外観設定を取得できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        settings = get_appearance_settings(config)

        assert settings['font_size'] == 11
        assert settings['log_font_size'] == 9
        assert settings['window_width'] == 350
        assert settings['window_height'] == 350


def test_get_dialog_settings(temp_config_file):
    """ダイアログ設定を取得できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        settings = get_dialog_settings(config)

        assert settings['folder_dialog_width'] == 600
        assert settings['folder_dialog_height'] == 200


def test_get_paths(temp_config_file):
    """パス設定を取得できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        paths = get_paths(config)

        assert paths['input_path'] == 'C:\\test\\input'
        assert paths['surgery_search_data'] == 'C:\\test\\search.csv'
        assert paths['output_path'] == 'C:\\test\\output'


def test_get_exclusion_line_keywords(temp_config_file):
    """行除外キーワードを取得できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        keywords = get_exclusion_line_keywords(config)

        assert '★' in keywords
        assert '霰粒腫' in keywords
        assert '術式未定' in keywords


def test_get_surgery_strings_to_remove(temp_config_file):
    """手術文字列削除リストを取得できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        strings = get_surgery_strings_to_remove(config)

        assert '(トーリック)' in strings
        assert '(inject)' in strings


def test_get_replacement_dict(temp_config_file):
    """置換辞書を取得できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        anesthesia = get_replacement_dict(config, 'Replacements', 'anesthesia_replacements')

        assert anesthesia['球後麻酔'] == '局所'
        assert anesthesia['点眼麻酔'] == '局所'


def test_get_replacement_dict_empty():
    """空の置換辞書を取得できる"""
    config = configparser.ConfigParser()
    config.add_section('Test')
    config.set('Test', 'empty', '')

    result = get_replacement_dict(config, 'Test', 'empty')
    assert result == {}


def test_save_replacement_dict(temp_config_file):
    """置換辞書を保存できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        new_dict = {'テスト1': '置換1', 'テスト2': '置換2'}

        save_replacement_dict(config, 'Replacements', 'anesthesia_replacements', new_dict)
        save_config(config)

        # 再読み込みして確認
        config2 = load_config()
        result = get_replacement_dict(config2, 'Replacements', 'anesthesia_replacements')
        assert result['テスト1'] == '置換1'
        assert result['テスト2'] == '置換2'


def test_save_exclusion_line_keywords(temp_config_file):
    """行除外キーワードを保存できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        new_keywords = ['キーワード1', 'キーワード2', 'キーワード3']

        save_exclusion_line_keywords(config, new_keywords)
        save_config(config)

        # 再読み込みして確認
        config2 = load_config()
        result = get_exclusion_line_keywords(config2)
        assert 'キーワード1' in result
        assert 'キーワード2' in result
        assert 'キーワード3' in result


def test_save_surgery_strings_to_remove(temp_config_file):
    """手術文字列削除リストを保存できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        new_strings = ['文字列1', '文字列2']

        save_surgery_strings_to_remove(config, new_strings)
        save_config(config)

        # 再読み込みして確認
        config2 = load_config()
        result = get_surgery_strings_to_remove(config2)
        assert '文字列1' in result
        assert '文字列2' in result
