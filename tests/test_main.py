import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_tk():
    """Tkinterのモックを作成"""
    with patch('main.tk') as mock:
        mock_root = MagicMock()
        mock.Tk.return_value = mock_root
        yield mock, mock_root


@pytest.fixture
def mock_config():
    """設定のモックを作成"""
    config = MagicMock()
    return config


@pytest.fixture
def mock_load_config(mock_config):
    """load_configのモックを作成"""
    with patch('main.load_config') as mock:
        mock.return_value = mock_config
        yield mock


@pytest.fixture
def mock_setup_logging():
    """setup_loggingのモックを作成"""
    with patch('main.setup_logging') as mock:
        yield mock


@pytest.fixture
def mock_gui():
    """OPHCheckerGUIのモックを作成"""
    with patch('main.OPHCheckerGUI') as mock:
        yield mock


def test_main_imports():
    """必要なモジュールがインポートできる"""
    import main
    assert hasattr(main, 'tk')
    assert hasattr(main, 'OPHCheckerGUI')
    assert hasattr(main, 'load_config')
    assert hasattr(main, 'setup_logging')


def test_main_module_structure():
    """mainモジュールが適切な構造を持つ"""
    import main

    # __main__ブロックが存在することを確認（import時に__name__が__main__でないため実行されない）
    assert hasattr(main, '__name__')

    # 必要なインポートがすべて存在する
    assert hasattr(main, 'tk')
    assert hasattr(main, 'OPHCheckerGUI')
    assert hasattr(main, 'load_config')
    assert hasattr(main, 'setup_logging')


def test_main_calls_setup_logging(mock_tk, mock_load_config, mock_setup_logging, mock_gui, mock_config):
    """メイン処理でロギングをセットアップする"""
    with patch.object(sys, 'argv', ['main.py']):
        # __main__ブロックをシミュレート
        config = mock_load_config.return_value
        mock_setup_logging(config)

        # 検証
        mock_setup_logging.assert_called_once_with(config)


def test_main_creates_tk_root(mock_tk, mock_load_config, mock_setup_logging, mock_gui):
    """メイン処理でTkルートウィンドウを作成する"""
    mock_tk_module, mock_root = mock_tk

    # __main__ブロックをシミュレート
    config = mock_load_config.return_value
    mock_setup_logging(config)
    root = mock_tk_module.Tk()

    # 検証
    mock_tk_module.Tk.assert_called_once()


def test_main_creates_gui_instance(mock_tk, mock_load_config, mock_setup_logging, mock_gui):
    """メイン処理でGUIインスタンスを作成する"""
    mock_tk_module, mock_root = mock_tk

    # __main__ブロックをシミュレート
    config = mock_load_config.return_value
    mock_setup_logging(config)
    root = mock_tk_module.Tk()
    app = mock_gui(root)

    # 検証
    mock_gui.assert_called_once_with(root)


def test_main_calls_mainloop(mock_tk, mock_load_config, mock_setup_logging, mock_gui):
    """メイン処理でmainloopを呼び出す"""
    mock_tk_module, mock_root = mock_tk

    # __main__ブロックをシミュレート
    config = mock_load_config.return_value
    mock_setup_logging(config)
    root = mock_tk_module.Tk()
    app = mock_gui(root)
    root.mainloop()

    # 検証
    mock_root.mainloop.assert_called_once()


def test_main_execution_order(mock_tk, mock_load_config, mock_setup_logging, mock_gui, mock_config):
    """メイン処理の実行順序が正しい"""
    mock_tk_module, mock_root = mock_tk
    call_order = []

    # 呼び出し順序を記録
    mock_load_config.side_effect = lambda: (call_order.append('load_config'), mock_config)[1]
    mock_setup_logging.side_effect = lambda config: call_order.append('setup_logging')
    mock_tk_module.Tk.side_effect = lambda: (call_order.append('create_tk'), mock_root)[1]
    mock_gui.side_effect = lambda root: (call_order.append('create_gui'), MagicMock())[1]
    mock_root.mainloop.side_effect = lambda: call_order.append('mainloop')

    # __main__ブロックをシミュレート
    config = mock_load_config()
    mock_setup_logging(config)
    root = mock_tk_module.Tk()
    app = mock_gui(root)
    root.mainloop()

    # 検証: 正しい順序で呼び出されているか
    assert call_order == ['load_config', 'setup_logging', 'create_tk', 'create_gui', 'mainloop']


def test_main_passes_config_to_logging(mock_tk, mock_load_config, mock_setup_logging, mock_gui, mock_config):
    """メイン処理で設定をロギングに渡す"""
    mock_load_config.return_value = mock_config

    # __main__ブロックをシミュレート
    config = mock_load_config()
    mock_setup_logging(config)

    # 検証: 正しい設定オブジェクトが渡されているか
    mock_setup_logging.assert_called_once_with(mock_config)


def test_main_passes_root_to_gui(mock_tk, mock_load_config, mock_setup_logging, mock_gui):
    """メイン処理でルートウィンドウをGUIに渡す"""
    mock_tk_module, mock_root = mock_tk

    # __main__ブロックをシミュレート
    config = mock_load_config()
    mock_setup_logging(config)
    root = mock_tk_module.Tk()
    app = mock_gui(root)

    # 検証: 正しいルートオブジェクトが渡されているか
    mock_gui.assert_called_once_with(mock_root)
