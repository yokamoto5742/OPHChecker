import tkinter as tk
from unittest.mock import patch

import pytest

from widgets.base_dialog import find_input_error
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

    dialog = ExcludeItemsDialog(root, keywords, strings)

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
    dialog = ExcludeItemsDialog(root, [], [])
    listbox = dialog.keywords_listbox
    item_list = dialog.exclusion_line_keywords

    with patch.object(dialog, '_ask_values', return_value=['新しいキーワード']):
        dialog._add_item(listbox, item_list, 'キーワード')

    assert item_list == ['新しいキーワード']
    assert listbox.get(0, tk.END) == ('新しいキーワード',)


def test_exclude_items_dialog_add_item_cancelled(root):
    """入力をキャンセルした場合は追加されない"""
    dialog = ExcludeItemsDialog(root, ['キーワード1'], [])

    with patch.object(dialog, '_ask_values', return_value=None):
        dialog._add_item(dialog.keywords_listbox, dialog.exclusion_line_keywords, 'キーワード')

    assert dialog.exclusion_line_keywords == ['キーワード1']
    assert dialog.keywords_listbox.size() == 1


def test_exclude_items_dialog_edit_item(root):
    """選択したアイテムを同じ位置で編集できる"""
    dialog = ExcludeItemsDialog(root, ['キーワード1', 'キーワード2'], [])
    listbox = dialog.keywords_listbox
    listbox.selection_set(0)

    with patch.object(dialog, '_ask_values', return_value=['変更後']) as mock_ask_values:
        dialog._edit_item(listbox, dialog.exclusion_line_keywords, 'キーワード')

    # 現在の値が初期値として渡される
    assert mock_ask_values.call_args.args[2] == ['キーワード1']
    assert dialog.exclusion_line_keywords == ['変更後', 'キーワード2']
    assert listbox.get(0, tk.END) == ('変更後', 'キーワード2')


def _operate_input_dialog(dialog: ExcludeItemsDialog, text: str, button_index: int) -> None:
    """_ask_valuesが開いた入力ダイアログに値を入れ、OK(0)またはキャンセル(1)を押す"""
    input_dialog = [widget for widget in dialog.dialog.winfo_children() if isinstance(widget, tk.Toplevel)][-1]
    try:
        entry = [widget for widget in input_dialog.winfo_children() if isinstance(widget, tk.Entry)][0]
        entry.delete(0, tk.END)
        entry.insert(0, text)
        button_frame = input_dialog.winfo_children()[-1]
        buttons = [widget for widget in button_frame.winfo_children() if isinstance(widget, tk.Button)]
        buttons[button_index].invoke()
    except Exception:
        input_dialog.destroy()
        raise


def test_ask_values_returns_stripped_input(root):
    """入力ダイアログでOKを押すと前後の空白を除いた値が返る"""
    dialog = ExcludeItemsDialog(root, [], [])
    root.after(50, lambda: _operate_input_dialog(dialog, ' (トーリック) ', 0))

    assert dialog._ask_values('キーワード追加', ['キーワード:'], ['']) == ['(トーリック)']


@pytest.mark.parametrize('invalid_text', ['', 'a,b', '10:30', '50%'])
def test_ask_values_rejects_invalid_input(root, invalid_text):
    """空欄や保存形式を壊す文字は警告して受け付けない"""
    dialog = ExcludeItemsDialog(root, [], [])

    with patch('tkinter.messagebox.showwarning') as mock_showwarning:
        root.after(50, lambda: _operate_input_dialog(dialog, invalid_text, 0))
        root.after(100, lambda: _operate_input_dialog(dialog, invalid_text, 1))

        assert dialog._ask_values('キーワード追加', ['キーワード:'], ['']) is None
        mock_showwarning.assert_called_once()


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


@pytest.mark.parametrize('value', ['a,b', '10:30', '50%', ''])
def test_find_input_error_rejects_invalid_values(value):
    """空欄や保存形式を壊す文字を含む入力はエラーになる"""
    assert find_input_error(['キーワード', value]) is not None


def test_find_input_error_accepts_normal_characters():
    """括弧などの通常の文字は拒否しない"""
    assert find_input_error(['(トーリック)', '★']) is None


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
