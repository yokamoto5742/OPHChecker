import configparser
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.config_manager import (
    get_appearance_settings,
    get_exclude_items,
    get_paths,
    get_replacements,
    load_config,
    save_config,
    save_exclude_items,
    save_replacements,
)


@pytest.fixture
def temp_config_file(tmp_path: Path) -> str:
    """一時的な設定ファイルを作成"""
    config_path = tmp_path / 'config.ini'
    config_path.write_text(f"""[Appearance]
font_size = 11
log_font_size = 9
window_width = 350
window_height = 350

[Paths]
input_path = C:\\test\\input
surgery_search_data = C:\\test\\search.csv
processed_surgery_search_data = C:\\test\\processed_search.csv
surgery_schedule = C:\\test\\schedule.xlsx
processed_surgery_schedule = C:\\test\\processed_schedule.csv
comparison_result = C:\\test\\comparison.csv
template_path = C:\\test\\template.xlsx
output_path = C:\\test\\output
excludeitems_file = {tmp_path / 'excludeitems.txt'}
replacements_file = {tmp_path / 'replacements.txt'}
""", encoding='utf-8')
    return str(config_path)


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


def test_get_paths(temp_config_file):
    """パス設定を取得できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        paths = get_paths(config)

        assert paths['input_path'] == 'C:\\test\\input'
        assert paths['surgery_search_data'] == 'C:\\test\\search.csv'
        assert paths['output_path'] == 'C:\\test\\output'


def test_get_exclude_items_returns_defaults_without_file(temp_config_file):
    """txtが無い場合は除外設定の既定値を取得できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        exclude_items = get_exclude_items(config)

        assert '★' in exclude_items['exclusion_line_keywords']
        assert '霰粒腫' in exclude_items['exclusion_line_keywords']
        assert '(トーリック)' in exclude_items['surgery_strings_to_remove']
        assert '(inject)' in exclude_items['surgery_strings_to_remove']


def test_get_replacements_returns_defaults_without_file(temp_config_file):
    """txtが無い場合は置換設定の既定値を取得できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        replacements = get_replacements(config)

        assert replacements['anesthesia_replacements']['球後麻酔'] == '局所'
        assert replacements['surgeon_replacements']['橋本義弘'] == '橋本'
        assert replacements['inpatient_replacements']['あやめ'] == '入院'


def test_get_replacements_empty_value(temp_config_file, tmp_path):
    """値が空の置換設定は空の辞書になる"""
    (tmp_path / 'replacements.txt').write_text(
        '[Replacements]\nanesthesia_replacements =\n', encoding='utf-8'
    )

    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()

        assert get_replacements(config)['anesthesia_replacements'] == {}


def test_broken_exclude_items_file_raises_and_is_not_overwritten(temp_config_file, tmp_path):
    """txtが存在するのに読めない場合は例外になり、既定値で上書きされない"""
    broken_text = 'セクションの無い行\n'
    exclude_items_file = tmp_path / 'excludeitems.txt'
    exclude_items_file.write_text(broken_text, encoding='utf-8')

    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()

        with pytest.raises(configparser.Error):
            get_exclude_items(config)
        with pytest.raises(configparser.Error):
            save_exclude_items(config, {'exclusion_line_keywords': ['キーワード1']})

    assert exclude_items_file.read_text(encoding='utf-8') == broken_text


def test_broken_replacements_file_raises(temp_config_file, tmp_path):
    """置換txtが存在するのに読めない場合は例外になる"""
    (tmp_path / 'replacements.txt').write_text('セクションの無い行\n', encoding='utf-8')

    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()

        with pytest.raises(configparser.Error):
            get_replacements(config)


def test_save_replacements(temp_config_file):
    """置換設定を保存できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        new_replacements = {
            'anesthesia_replacements': {'テスト1': '置換1', 'テスト2': '置換2'},
            'surgeon_replacements': {'医師1': '置換3'},
            'inpatient_replacements': {},
        }

        save_replacements(config, new_replacements)

        assert get_replacements(load_config()) == new_replacements


def test_save_exclude_items(temp_config_file):
    """除外設定を保存できる"""
    with patch('utils.config_manager.CONFIG_PATH', temp_config_file):
        config = load_config()
        new_exclude_items = {
            'exclusion_line_keywords': ['キーワード1', 'キーワード2', 'キーワード3'],
            'surgery_strings_to_remove': ['文字列1', '文字列2'],
        }

        save_exclude_items(config, new_exclude_items)

        assert get_exclude_items(load_config()) == new_exclude_items


def test_save_without_file_path_raises():
    """txtのパスが未設定の場合は保存できない"""
    with pytest.raises(ValueError):
        save_exclude_items(configparser.ConfigParser(), {'exclusion_line_keywords': ['キーワード1']})
