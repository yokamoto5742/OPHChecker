import tkinter as tk
from unittest.mock import patch

import pytest

from widgets.replacements_dialog import ReplacementsDialog


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


def test_replacements_dialog_init(root):
    """ダイアログが初期化される"""
    anesthesia = {'球後麻酔': '局所'}
    surgeon = {'橋本義弘': '橋本'}
    inpatient = {'あやめ': '入院'}

    dialog = ReplacementsDialog(root, anesthesia, surgeon, inpatient)

    assert dialog.parent == root
    assert dialog.anesthesia_replacements == anesthesia
    assert dialog.surgeon_replacements == surgeon
    assert dialog.inpatient_replacements == inpatient
    assert dialog.result is None


def test_replacements_dialog_show_returns_none_on_cancel(root):
    """キャンセル時にNoneを返す"""
    anesthesia = {'球後麻酔': '局所'}
    surgeon = {}
    inpatient = {}

    dialog = ReplacementsDialog(root, anesthesia, surgeon, inpatient)

    # キャンセルをシミュレート
    dialog._cancel()

    assert dialog.result is None


def test_replacements_dialog_show_returns_result_on_save(root):
    """保存時に結果を返す"""
    anesthesia = {'球後麻酔': '局所'}
    surgeon = {'橋本義弘': '橋本'}
    inpatient = {'あやめ': '入院'}

    dialog = ReplacementsDialog(root, anesthesia, surgeon, inpatient)

    # 保存をシミュレート
    dialog._save()

    assert dialog.result is not None
    assert 'anesthesia_replacements' in dialog.result
    assert 'surgeon_replacements' in dialog.result
    assert 'inpatient_replacements' in dialog.result


def test_replacements_dialog_add_replacement(root):
    """置換を追加できる"""
    dialog = ReplacementsDialog(root, {'球後麻酔': '局所'}, {}, {})

    with patch.object(dialog, '_ask_values', return_value=['点眼麻酔', '局所']):
        dialog._add_replacement(dialog.anesthesia_listbox, dialog.anesthesia_replacements)

    assert dialog.anesthesia_replacements == {'球後麻酔': '局所', '点眼麻酔': '局所'}
    assert dialog.anesthesia_listbox.get(tk.END) == '点眼麻酔 → 局所'


def test_replacements_dialog_edit_replacement_keeps_position(root):
    """キーを変更しても辞書とリストボックスの並び順が変わらない"""
    dialog = ReplacementsDialog(root, {'球後麻酔': '局所', '全身麻酔': '全身'}, {}, {})
    listbox = dialog.anesthesia_listbox
    listbox.selection_set(0)

    with patch.object(dialog, '_ask_values', return_value=['テノン嚢下', '局所']) as mock_ask_values:
        dialog._edit_replacement(listbox, dialog.anesthesia_replacements)

    # 現在のキーと値が初期値として渡される
    assert mock_ask_values.call_args.args[2] == ['球後麻酔', '局所']
    assert list(dialog.anesthesia_replacements.items()) == [('テノン嚢下', '局所'), ('全身麻酔', '全身')]
    assert listbox.get(0, tk.END) == ('テノン嚢下 → 局所', '全身麻酔 → 全身')


def test_replacements_dialog_rejects_duplicate_key(root):
    """他の項目と置換前が重複する入力はエラーになる（自分自身の編集は除く）"""
    dialog = ReplacementsDialog(root, {'球後麻酔': '局所', '全身麻酔': '全身'}, {}, {})

    with patch.object(dialog, '_ask_values') as mock_ask_values:
        dialog._ask_replacement('置換編集', '球後麻酔', '局所', dialog.anesthesia_replacements)

    find_duplicate = mock_ask_values.call_args.args[3]
    assert find_duplicate(['全身麻酔', '局所']) is not None
    assert find_duplicate(['球後麻酔', '全身']) is None
    assert find_duplicate(['点眼麻酔', '局所']) is None


def test_replacements_dialog_delete_replacement_with_arrow_in_value(root):
    """値に「 → 」を含む置換も削除できる"""
    dialog = ReplacementsDialog(root, {'A': 'B → C'}, {}, {})
    listbox = dialog.anesthesia_listbox
    listbox.selection_set(0)

    with patch('tkinter.messagebox.askyesno', return_value=True):
        dialog._delete_replacement(listbox, dialog.anesthesia_replacements)

    assert dialog.anesthesia_replacements == {}
    assert listbox.size() == 0


def test_replacements_dialog_delete_replacement(root):
    """置換を削除できる"""
    anesthesia = {'球後麻酔': '局所', '点眼麻酔': '局所'}
    surgeon = {}
    inpatient = {}

    dialog = ReplacementsDialog(root, anesthesia, surgeon, inpatient)

    listbox = dialog.anesthesia_listbox
    replacements_dict = dialog.anesthesia_replacements

    # 最初のアイテムを選択
    listbox.selection_set(0)

    # モック確認ダイアログ
    with patch('tkinter.messagebox.askyesno') as mock_askyesno:
        mock_askyesno.return_value = True

        dialog._delete_replacement(listbox, replacements_dict)

    # アイテムが削除される
    assert '球後麻酔' not in replacements_dict
    assert listbox.size() == 1


def test_replacements_dialog_delete_replacement_no_selection(root):
    """選択なしで削除すると警告が表示される"""
    anesthesia = {'球後麻酔': '局所'}
    surgeon = {}
    inpatient = {}

    dialog = ReplacementsDialog(root, anesthesia, surgeon, inpatient)

    listbox = dialog.anesthesia_listbox
    replacements_dict = dialog.anesthesia_replacements

    # 選択なし
    with patch('tkinter.messagebox.showwarning') as mock_showwarning:
        dialog._delete_replacement(listbox, replacements_dict)

        # 警告が表示される
        mock_showwarning.assert_called_once()


def test_replacements_dialog_has_three_tabs(root):
    """3つのタブがある"""
    anesthesia = {}
    surgeon = {}
    inpatient = {}

    dialog = ReplacementsDialog(root, anesthesia, surgeon, inpatient)

    # 3つのリストボックスが作成されていることを確認
    assert hasattr(dialog, 'anesthesia_listbox')
    assert hasattr(dialog, 'surgeon_listbox')
    assert hasattr(dialog, 'inpatient_listbox')


def test_replacements_dialog_copies_dicts(root):
    """辞書がコピーされる（元の辞書は変更されない）"""
    original_anesthesia = {'球後麻酔': '局所'}
    original_surgeon = {'橋本義弘': '橋本'}
    original_inpatient = {'あやめ': '入院'}

    dialog = ReplacementsDialog(root, original_anesthesia, original_surgeon, original_inpatient)

    # ダイアログ内で辞書を変更
    dialog.anesthesia_replacements['新しい麻酔'] = '新しい値'
    dialog.surgeon_replacements['新しい医師'] = '新しい値'
    dialog.inpatient_replacements['新しい入外'] = '新しい値'

    # 元の辞書は変更されない
    assert '新しい麻酔' not in original_anesthesia
    assert '新しい医師' not in original_surgeon
    assert '新しい入外' not in original_inpatient


def test_replacements_dialog_listbox_format(root):
    """リストボックスの表示形式が正しい"""
    anesthesia = {'球後麻酔': '局所', '点眼麻酔': '局所'}
    surgeon = {}
    inpatient = {}

    dialog = ReplacementsDialog(root, anesthesia, surgeon, inpatient)

    listbox = dialog.anesthesia_listbox

    # リストボックスの内容を確認
    items = [listbox.get(i) for i in range(listbox.size())]

    assert '球後麻酔 → 局所' in items
    assert '点眼麻酔 → 局所' in items
