import configparser
import logging
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.log_rotation import cleanup_old_logs, setup_logging


@pytest.fixture
def temp_log_directory():
    """一時的なログディレクトリを作成"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    # クリーンアップ
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass


@pytest.fixture
def temp_config():
    """一時的な設定オブジェクトを作成"""
    config = configparser.ConfigParser()
    config.add_section('LOGGING')
    config.set('LOGGING', 'log_directory', 'test_logs')
    config.set('LOGGING', 'log_retention_days', '7')
    return config


def test_cleanup_old_logs_removes_old_files(temp_log_directory):
    """古いログファイルが削除される"""
    # 古いログファイルを作成
    old_log = Path(temp_log_directory) / 'old_2020-01-01.log'
    old_log.write_text('old log content', encoding='utf-8')

    # ファイルの更新日時を古い日付に設定
    old_time = (datetime.now() - timedelta(days=10)).timestamp()
    os.utime(old_log, (old_time, old_time))

    # 新しいログファイルを作成
    new_log = Path(temp_log_directory) / 'new.log'
    new_log.write_text('new log content', encoding='utf-8')

    # メインログファイルを作成
    main_log = Path(temp_log_directory) / 'test_logs.log'
    main_log.write_text('main log content', encoding='utf-8')

    # クリーンアップを実行（保持期間7日）
    cleanup_old_logs(temp_log_directory, 7)

    # 古いログファイルが削除され、新しいログファイルは残る
    assert not old_log.exists()
    assert new_log.exists()
    assert main_log.exists()


def test_cleanup_old_logs_keeps_recent_files(temp_log_directory):
    """新しいログファイルは保持される"""
    # 新しいログファイルを作成
    recent_log = Path(temp_log_directory) / 'recent.log'
    recent_log.write_text('recent log content', encoding='utf-8')

    # クリーンアップを実行（保持期間7日）
    cleanup_old_logs(temp_log_directory, 7)

    # 新しいログファイルが残る
    assert recent_log.exists()


def test_cleanup_old_logs_preserves_main_log(temp_log_directory):
    """メインログファイルは常に保持される"""
    # 親ディレクトリ名に基づいたメインログファイル名を作成
    # cleanup_old_logsは親ディレクトリの親ディレクトリの名前を使用する
    parent_name = Path(temp_log_directory).parent.parent.name
    main_log = Path(temp_log_directory) / f'{parent_name}.log'
    main_log.write_text('main log content', encoding='utf-8')

    # ファイルの更新日時を古い日付に設定
    old_time = (datetime.now() - timedelta(days=100)).timestamp()
    os.utime(main_log, (old_time, old_time))

    # クリーンアップを実行
    cleanup_old_logs(temp_log_directory, 7)

    # メインログファイルは削除されない
    assert main_log.exists()


def test_setup_logging_creates_log_directory(temp_config):
    """ログディレクトリが作成される"""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir) / 'test_logs'
        temp_config.set('LOGGING', 'log_directory', str(log_dir))

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('utils.log_rotation.os.path.dirname', lambda x: temp_dir)
            setup_logging(temp_config)

        assert log_dir.exists()
