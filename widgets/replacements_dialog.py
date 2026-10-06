import tkinter as tk
from tkinter import messagebox, ttk

from widgets.base_dialog import BaseDialog


class ReplacementsDialog(BaseDialog):
    def __init__(self, parent: tk.Tk, anesthesia_replacements: dict[str, str],
                 surgeon_replacements: dict[str, str], inpatient_replacements: dict[str, str],
                 font_size: int = 11) -> None:
        self.anesthesia_replacements = anesthesia_replacements.copy()
        self.surgeon_replacements = surgeon_replacements.copy()
        self.inpatient_replacements = inpatient_replacements.copy()
        super().__init__(parent, "置換設定", font_size)

    def _setup_ui(self) -> None:
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        anesthesia_frame = tk.Frame(notebook)
        notebook.add(anesthesia_frame, text="麻酔")
        self.anesthesia_listbox = self._setup_replacements_tab(anesthesia_frame, self.anesthesia_replacements)

        surgeon_frame = tk.Frame(notebook)
        notebook.add(surgeon_frame, text="医師")
        self.surgeon_listbox = self._setup_replacements_tab(surgeon_frame, self.surgeon_replacements)

        inpatient_frame = tk.Frame(notebook)
        notebook.add(inpatient_frame, text="入外")
        self.inpatient_listbox = self._setup_replacements_tab(inpatient_frame, self.inpatient_replacements)

        self._create_button_frame()

    def _setup_replacements_tab(self, parent: tk.Frame, replacements_dict: dict[str, str]) -> tk.Listbox:
        description = tk.Label(
            parent,
            text="置換前 → 置換後",
            font=("Arial", self.font_size - 1),
            anchor="w",
        )
        description.pack(fill=tk.X, padx=10, pady=(10, 5))

        listbox = self._create_listbox_with_scrollbar(parent)

        for key, value in replacements_dict.items():
            listbox.insert(tk.END, f"{key} → {value}")

        self._create_action_buttons(
            parent,
            lambda: self._add_replacement(listbox, replacements_dict),
            lambda: self._edit_replacement(listbox, replacements_dict),
            lambda: self._delete_replacement(listbox, replacements_dict),
        )
        return listbox

    def _ask_replacement(
        self, title: str, current_key: str, current_value: str, replacements_dict: dict[str, str]
    ) -> list[str] | None:
        """置換前・置換後の入力ダイアログを表示（他の項目と置換前が重複する入力は受け付けない）"""
        def find_duplicate(values: list[str]) -> str | None:
            if values[0] != current_key and values[0] in replacements_dict:
                return "同じ値が既に存在します"
            return None

        return self._ask_values(title, ["置換前:", "置換後:"], [current_key, current_value], find_duplicate)

    def _add_replacement(self, listbox: tk.Listbox, replacements_dict: dict[str, str]) -> None:
        values = self._ask_replacement("置換追加", '', '', replacements_dict)
        if values:
            key, value = values
            replacements_dict[key] = value
            listbox.insert(tk.END, f"{key} → {value}")

    def _edit_replacement(self, listbox: tk.Listbox, replacements_dict: dict[str, str]) -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "編集する項目を選択してください", parent=self.dialog)
            return

        index = selection[0]
        current_key = list(replacements_dict)[index]
        values = self._ask_replacement("置換編集", current_key, replacements_dict[current_key], replacements_dict)
        if values:
            new_key, new_value = values
            # キーを変えても並び順が変わらないよう、同じ位置で入れ替える
            replacement_items = list(replacements_dict.items())
            replacement_items[index] = (new_key, new_value)
            replacements_dict.clear()
            replacements_dict.update(replacement_items)

            listbox.delete(index)
            listbox.insert(index, f"{new_key} → {new_value}")
            listbox.selection_set(index)

    def _delete_replacement(self, listbox: tk.Listbox, replacements_dict: dict[str, str]) -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除する項目を選択してください", parent=self.dialog)
            return

        index = selection[0]

        if messagebox.askyesno("確認", f"「{listbox.get(index)}」を削除しますか?", parent=self.dialog):
            del replacements_dict[list(replacements_dict)[index]]
            listbox.delete(index)

    def _save(self) -> None:
        self.result = {
            'anesthesia_replacements': self.anesthesia_replacements,
            'surgeon_replacements': self.surgeon_replacements,
            'inpatient_replacements': self.inpatient_replacements,
        }
        self.dialog.destroy()
