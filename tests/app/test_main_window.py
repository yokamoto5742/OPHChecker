import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from app.main_window import OPHCheckerGUI


@pytest.fixture
def root():
    """Tkルートウィンドウを作成"""
    root_window = tk.Tk()
    root_window.withdraw()
    yield root_window
    try:
        root_window.destroy()
    except:
        pass


@pytest.fixture
def mock_config():
    """モック設定を作成"""
    config = MagicMock()
    config.getint.side_effect = lambda section, key, fallback=None: {
        ('Appearance', 'font_size'): 11,
        ('Appearance', 'log_font_size'): 9,
        ('Appearance', 'window_width'): 350,
        ('Appearance', 'window_height'): 350,
    }.get((section, key), fallback)

    config.get.side_effect = lambda section, key, fallback='': {
        ('Paths', 'surgery_search_data'): 'C:\\test\\search.csv',
        ('Paths', 'surgery_schedule'): 'C:\\test\\schedule.xlsx',
        ('Paths', 'template_path'): 'C:\\test\\template.xlsx',
        ('Paths', 'output_path'): 'C:\\test\\output',
        ('Paths', 'input_path'): 'C:\\test\\input',
    }.get((section, key), fallback)

    return config


def test_oph_checker_gui_init(root, mock_config):
    """GUIが初期化される"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        gui = OPHCheckerGUI(root)

        assert gui.root == root
        assert gui.config == mock_config
        assert hasattr(gui, 'start_button')
        assert hasattr(gui, 'log_text')


def test_oph_checker_gui_window_title(root, mock_config):
    """ウィンドウタイトルにバージョンが含まれる"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config
        with patch('app.main_window.__version__', '1.0.0'):
            gui = OPHCheckerGUI(root)

            assert '眼科手術指示確認 v1.0.0' in root.title()


def test_oph_checker_gui_log_message(root, mock_config):
    """ログメッセージが追加される"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        gui = OPHCheckerGUI(root)
        gui._log_message('テストメッセージ')

        log_content = gui.log_text.get('1.0', tk.END)
        assert 'テストメッセージ' in log_content


def test_oph_checker_gui_validate_config_success(root, mock_config):
    """設定検証が成功する"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True

            gui = OPHCheckerGUI(root)
            result = gui._validate_config()

            assert result is True


def test_oph_checker_gui_validate_config_missing_file(root, mock_config):
    """ファイルが存在しない場合は検証失敗"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            with patch('tkinter.messagebox.showerror') as mock_error:
                gui = OPHCheckerGUI(root)
                result = gui._validate_config()

                assert result is False
                mock_error.assert_called()


def test_oph_checker_gui_validate_config_allows_missing_output_folder(root, mock_config):
    """出力フォルダが無くても入力ファイルがあれば検証は成功する"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        with patch('pathlib.Path.exists', autospec=True) as mock_exists:
            mock_exists.side_effect = lambda path: str(path) != 'C:\\test\\output'

            gui = OPHCheckerGUI(root)

            assert gui._validate_config() is True


def test_oph_checker_gui_validate_config_requires_template(root, mock_config):
    """テンプレートが無い場合は検証失敗"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        with patch('pathlib.Path.exists', autospec=True) as mock_exists:
            mock_exists.side_effect = lambda path: str(path) != 'C:\\test\\template.xlsx'

            with patch('tkinter.messagebox.showerror') as mock_error:
                gui = OPHCheckerGUI(root)

                assert gui._validate_config() is False
                mock_error.assert_called_once()


def test_oph_checker_gui_create_output_folders(root, mock_config, tmp_path):
    """出力先フォルダが無ければ作成される"""
    paths = {
        'output_path': str(tmp_path / 'output'),
        'processed_surgery_schedule': str(tmp_path / 'processed' / 'schedule.csv'),
        'processed_surgery_search_data': str(tmp_path / 'processed' / 'search.csv'),
        'comparison_result': str(tmp_path / 'comparison' / 'result.csv'),
    }
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        gui = OPHCheckerGUI(root)
        gui._create_output_folders(paths)

    assert (tmp_path / 'output').is_dir()
    assert (tmp_path / 'processed').is_dir()
    assert (tmp_path / 'comparison').is_dir()


def test_oph_checker_gui_completion_summary_with_no_rows(root, mock_config, tmp_path):
    """除外の結果0件でも完了サマリーでエラーにならない"""
    empty_csv = tmp_path / 'processed_search.csv'
    empty_csv.write_text('手術日,患者ID\n', encoding='cp932')

    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        gui = OPHCheckerGUI(root)
        gui._log_completion_summary(str(empty_csv))

        assert '対象データはありませんでした' in gui.log_text.get('1.0', tk.END)
        assert gui.status_var.get() == '処理完了'


def test_oph_checker_gui_start_analysis_validates_config(root, mock_config):
    """分析開始時に設定を検証する"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            with patch('tkinter.messagebox.showerror'):
                gui = OPHCheckerGUI(root)
                gui._start_analysis()

                # ボタンは無効化されない（検証失敗のため）
                assert str(gui.start_button['state']) == 'normal'


def test_oph_checker_gui_start_analysis_runs_all_steps_synchronously(root, mock_config):
    """分析はメインスレッドで4処理を順に実行し、完了後にボタンが有効に戻る"""
    called_steps: list[str] = []

    def record_step(step_name: str, return_value: str | None = None):
        return lambda *args: called_steps.append(step_name) or return_value

    with (
        patch('app.main_window.load_config', return_value=mock_config),
        patch('app.main_window.process_surgery_schedule', side_effect=record_step('schedule')),
        patch('app.main_window.process_eye_surgery_data', side_effect=record_step('search')),
        patch('app.main_window.compare_surgery_data', side_effect=record_step('compare')),
        patch('app.main_window.surgery_error_extractor', side_effect=record_step('extract', 'output.xlsx')),
        patch('app.main_window.read_csv_rows', return_value=[{'手術日': '2025/01/15'}]),
        patch('app.main_window.os.startfile') as mock_startfile,
    ):
        gui = OPHCheckerGUI(root)
        with (
            patch.object(gui, '_validate_config', return_value=True),
            patch.object(gui, '_create_output_folders'),
        ):
            gui._start_analysis()

        # スレッドを使わないので、戻った時点ですべて完了している
        assert called_steps == ['schedule', 'search', 'compare', 'extract']
        assert gui.status_var.get() == '処理完了'
        assert str(gui.start_button['state']) == 'normal'
        mock_startfile.assert_called_once()


def test_oph_checker_gui_start_analysis_shows_error_when_step_fails(root, mock_config):
    """処理が失敗したらエラーを表示し、後続の処理は実行しない"""
    with (
        patch('app.main_window.load_config', return_value=mock_config),
        patch('app.main_window.process_surgery_schedule', side_effect=ValueError('読み込み失敗')),
        patch('app.main_window.process_eye_surgery_data') as mock_search,
        patch('tkinter.messagebox.showerror') as mock_error,
    ):
        gui = OPHCheckerGUI(root)
        with (
            patch.object(gui, '_validate_config', return_value=True),
            patch.object(gui, '_create_output_folders'),
        ):
            gui._start_analysis()

        mock_search.assert_not_called()
        mock_error.assert_called_once()
        assert '読み込み失敗' in gui.status_var.get()
        assert str(gui.start_button['state']) == 'normal'


def test_oph_checker_gui_close_application_while_running(root, mock_config):
    """実行中にアプリケーションを閉じると警告が表示される"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        gui = OPHCheckerGUI(root)
        gui.start_button.config(state=tk.DISABLED)

        with patch('tkinter.messagebox.showwarning') as mock_warning:
            gui._close_application()

            mock_warning.assert_called_once()


def test_oph_checker_gui_close_application_when_idle(root, mock_config):
    """アイドル時にアプリケーションを閉じる"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        gui = OPHCheckerGUI(root)

        # quitメソッドをモック
        root.quit = MagicMock()

        gui._close_application()

        root.quit.assert_called_once()


def test_oph_checker_gui_copy_input_path_to_clipboard(root, mock_config):
    """入力パスをクリップボードにコピーできる"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        gui = OPHCheckerGUI(root)

        # クリップボード操作をモック
        root.clipboard_clear = MagicMock()
        root.clipboard_append = MagicMock()

        gui._copy_input_path_to_clipboard()

        root.clipboard_clear.assert_called_once()
        root.clipboard_append.assert_called_once()


def test_oph_checker_gui_copy_input_path_missing(root, mock_config):
    """入力パスが設定されていない場合は警告が表示される"""
    # 入力パスなしの設定
    config_no_input = MagicMock()
    config_no_input.getint.side_effect = lambda section, key, fallback=None: {
        ('Appearance', 'font_size'): 11,
        ('Appearance', 'log_font_size'): 9,
        ('Appearance', 'window_width'): 350,
        ('Appearance', 'window_height'): 350,
    }.get((section, key), fallback)

    config_no_input.get.side_effect = lambda section, key, fallback='': {
        ('Paths', 'input_path'): '',  # 空
    }.get((section, key), fallback)

    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = config_no_input

        gui = OPHCheckerGUI(root)

        with patch('tkinter.messagebox.showwarning') as mock_warning:
            gui._copy_input_path_to_clipboard()

            mock_warning.assert_called_once()


def test_oph_checker_gui_open_exclude_items(root, mock_config):
    """除外項目ダイアログを開く"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        with patch('app.main_window.get_exclude_items') as mock_get_exclude_items:
            mock_get_exclude_items.return_value = {
                'exclusion_line_keywords': [],
                'surgery_strings_to_remove': [],
            }

            with patch('app.main_window.ExcludeItemsDialog') as mock_dialog:
                mock_dialog_instance = MagicMock()
                mock_dialog_instance.show.return_value = None  # キャンセル
                mock_dialog.return_value = mock_dialog_instance

                gui = OPHCheckerGUI(root)
                gui._open_exclude_items()

                mock_dialog.assert_called_once()


def test_oph_checker_gui_open_replacements(root, mock_config):
    """置換設定ダイアログを開く"""
    with patch('app.main_window.load_config') as mock_load_config:
        mock_load_config.return_value = mock_config

        with patch('app.main_window.get_replacements') as mock_get_replacements:
            mock_get_replacements.return_value = {
                'anesthesia_replacements': {},
                'surgeon_replacements': {},
                'inpatient_replacements': {},
            }

            with patch('app.main_window.ReplacementsDialog') as mock_dialog:
                mock_dialog_instance = MagicMock()
                mock_dialog_instance.show.return_value = None  # キャンセル
                mock_dialog.return_value = mock_dialog_instance

                gui = OPHCheckerGUI(root)
                gui._open_replacements()

                mock_dialog.assert_called_once()
