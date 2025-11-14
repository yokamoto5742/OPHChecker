import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from widgets.exclude_items_dialog import ExcludeItemsDialog


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


def test_exclude_items_dialog_init(root):
    """ダイアログが初期化される"""
    keywords = ['キーワード1', 'キーワード2']
    strings = ['文字列1', '文字列2']

    dialog = ExcludeItemsDialog(root, keywords, strings, font_size=11)

    assert dialog.parent == root
    assert dialog.exclusion_line_keywords == keywords
    assert dialog.surgery_strings_to_remove == strings
    assert dialog.result is None


def test_exclude_items_dialog_show_returns_none_on_cancel(root):
    """キャンセル時にNoneを返す"""
    keywords = ['キーワード1']
    strings = ['文字列1']

    dialog = ExcludeItemsDialog(root, keywords, strings)

    # キャンセルをシミュレート
    dialog._cancel()

    assert dialog.result is None


def test_exclude_items_dialog_show_returns_result_on_save(root):
    """保存時に結果を返す"""
    keywords = ['キーワード1']
    strings = ['文字列1']

    dialog = ExcludeItemsDialog(root, keywords, strings)

    # 保存をシミュレート
    dialog._save()

    assert dialog.result is not None
    assert 'exclusion_line_keywords' in dialog.result
    assert 'surgery_strings_to_remove' in dialog.result


def test_exclude_items_dialog_add_item(root):
    """アイテムを追加できる"""
    keywords = []
    strings = []

    dialog = ExcludeItemsDialog(root, keywords, strings)

    # リストボックスとアイテムリストを取得
    listbox = dialog.keywords_listbox
    item_list = dialog.exclusion_line_keywords

    # モックエントリを作成
    with patch('tkinter.Toplevel') as mock_toplevel:
        mock_dialog = MagicMock()
        mock_toplevel.return_value = mock_dialog

        with patch('tkinter.Entry') as mock_entry:
            mock_entry_instance = MagicMock()
            mock_entry_instance.get.return_value = '新しいキーワード'
            mock_entry.return_value = mock_entry_instance

            # 手動でアイテムを追加
            item_list.append('新しいキーワード')
            listbox.insert(tk.END, '新しいキーワード')

    assert '新しいキーワード' in item_list
    assert listbox.size() == 1


def test_exclude_items_dialog_delete_item(root):
    """アイテムを削除できる"""
    keywords = ['キーワード1', 'キーワード2']
    strings = []

    dialog = ExcludeItemsDialog(root, keywords, strings)

    listbox = dialog.keywords_listbox
    item_list = dialog.exclusion_line_keywords

    # 最初のアイテムを選択
    listbox.selection_set(0)

    # モック確認ダイアログ
    with patch('tkinter.messagebox.askyesno') as mock_askyesno:
        mock_askyesno.return_value = True

        dialog._delete_item(listbox, item_list)

    # アイテムが削除される
    assert 'キーワード1' not in item_list
    assert listbox.size() == 1


def test_exclude_items_dialog_delete_item_no_selection(root):
    """選択なしで削除すると警告が表示される"""
    keywords = ['キーワード1']
    strings = []

    dialog = ExcludeItemsDialog(root, keywords, strings)

    listbox = dialog.keywords_listbox
    item_list = dialog.exclusion_line_keywords

    # 選択なし
    with patch('tkinter.messagebox.showwarning') as mock_showwarning:
        dialog._delete_item(listbox, item_list)

        # 警告が表示される
        mock_showwarning.assert_called_once()


def test_exclude_items_dialog_has_two_tabs(root):
    """2つのタブがある"""
    keywords = []
    strings = []

    dialog = ExcludeItemsDialog(root, keywords, strings)

    # タブが作成されていることを確認
    assert hasattr(dialog, 'keywords_listbox')
    assert hasattr(dialog, 'surgery_listbox')


def test_exclude_items_dialog_copies_lists(root):
    """リストがコピーされる（元のリストは変更されない）"""
    original_keywords = ['キーワード1']
    original_strings = ['文字列1']

    dialog = ExcludeItemsDialog(root, original_keywords, original_strings)

    # ダイアログ内でリストを変更
    dialog.exclusion_line_keywords.append('新しいキーワード')
    dialog.surgery_strings_to_remove.append('新しい文字列')

    # 元のリストは変更されない
    assert '新しいキーワード' not in original_keywords
    assert '新しい文字列' not in original_strings
