import configparser
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from utils.file_cleaner import cleanup_old_files


@pytest.fixture
def temp_output_directory():
    """一時的な出力ディレクトリを作成"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass


@pytest.fixture
def temp_config(temp_output_directory):
    """一時的な設定オブジェクトを作成"""
    config = configparser.ConfigParser()
    config.add_section('FileCleanup')
    config.set('FileCleanup', 'enabled', 'true')
    config.set('FileCleanup', 'retention_days', '1')
    config.add_section('Paths')
    config.set('Paths', 'output_path', temp_output_directory)
    return config


def test_cleanup_old_files_removes_old_files(temp_config, temp_output_directory):
    """古いファイルが削除される"""
    old_file = Path(temp_output_directory) / 'old_file.xlsx'
    old_file.write_text('old content', encoding='utf-8')

    old_time = (datetime.now() - timedelta(days=2)).timestamp()
    os.utime(old_file, (old_time, old_time))

    new_file = Path(temp_output_directory) / 'new_file.xlsx'
    new_file.write_text('new content', encoding='utf-8')

    cleanup_old_files(temp_config)

    assert not old_file.exists()
    assert new_file.exists()


def test_cleanup_old_files_keeps_recent_files(temp_config, temp_output_directory):
    """新しいファイルは保持される"""
    recent_file = Path(temp_output_directory) / 'recent_file.xlsx'
    recent_file.write_text('recent content', encoding='utf-8')

    cleanup_old_files(temp_config)

    assert recent_file.exists()


def test_cleanup_old_files_disabled(temp_config, temp_output_directory):
    """クリーンアップが無効の場合、ファイルは削除されない"""
    temp_config.set('FileCleanup', 'enabled', 'false')

    old_file = Path(temp_output_directory) / 'old_file.xlsx'
    old_file.write_text('old content', encoding='utf-8')

    old_time = (datetime.now() - timedelta(days=10)).timestamp()
    os.utime(old_file, (old_time, old_time))

    cleanup_old_files(temp_config)

    assert old_file.exists()


def test_cleanup_old_files_respects_retention_days(temp_config, temp_output_directory):
    """retention_daysの設定が正しく反映される"""
    temp_config.set('FileCleanup', 'retention_days', '3')

    two_days_old = Path(temp_output_directory) / 'two_days_old.xlsx'
    two_days_old.write_text('content', encoding='utf-8')
    two_days_old_time = (datetime.now() - timedelta(days=2)).timestamp()
    os.utime(two_days_old, (two_days_old_time, two_days_old_time))

    four_days_old = Path(temp_output_directory) / 'four_days_old.xlsx'
    four_days_old.write_text('content', encoding='utf-8')
    four_days_old_time = (datetime.now() - timedelta(days=4)).timestamp()
    os.utime(four_days_old, (four_days_old_time, four_days_old_time))

    cleanup_old_files(temp_config)

    assert two_days_old.exists()
    assert not four_days_old.exists()


def test_cleanup_old_files_nonexistent_directory(temp_config):
    """存在しないディレクトリの場合、エラーが発生しない"""
    temp_config.set('Paths', 'output_path', 'C:\\nonexistent\\directory')

    cleanup_old_files(temp_config)


def test_cleanup_old_files_ignores_subdirectories(temp_config, temp_output_directory):
    """サブディレクトリは削除対象外"""
    subdir = Path(temp_output_directory) / 'subdir'
    subdir.mkdir()

    old_time = (datetime.now() - timedelta(days=10)).timestamp()
    os.utime(subdir, (old_time, old_time))

    cleanup_old_files(temp_config)

    assert subdir.exists()
