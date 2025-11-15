import tkinter as tk
from tkinter import messagebox, ttk

from widgets.base_dialog import BaseDialog


class ExcludeItemsDialog(BaseDialog):
    def __init__(self, parent: tk.Tk, exclusion_line_keywords: list[str], surgery_strings_to_remove: list[str], font_size: int = 11) -> None:
        self.exclusion_line_keywords = exclusion_line_keywords.copy()
        self.surgery_strings_to_remove = surgery_strings_to_remove.copy()
        super().__init__(parent, "除外設定", font_size)

    def _setup_ui(self) -> None:
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        keywords_frame = tk.Frame(notebook)
        notebook.add(keywords_frame, text="行除外キーワード")
        self._setup_keywords_tab(keywords_frame)

        surgery_frame = tk.Frame(notebook)
        notebook.add(surgery_frame, text="手術文字列削除")
        self._setup_surgery_tab(surgery_frame)

        self._create_button_frame()

    def _setup_keywords_tab(self, parent: tk.Frame) -> None:
        description = tk.Label(
            parent,
            text="以下のキーワードを含む行は除外されます",
            font=("Arial", self.font_size - 1),
            anchor="w",
        )
        description.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.keywords_listbox = self._create_listbox_with_scrollbar(parent)

        for keyword in self.exclusion_line_keywords:
            self.keywords_listbox.insert(tk.END, keyword)

        self._create_action_buttons(
            parent,
            lambda: self._add_item(self.keywords_listbox, self.exclusion_line_keywords, "キーワード"),
            lambda: self._edit_item(self.keywords_listbox, self.exclusion_line_keywords, "キーワード"),
            lambda: self._delete_item(self.keywords_listbox, self.exclusion_line_keywords),
        )

    def _setup_surgery_tab(self, parent: tk.Frame) -> None:
        description = tk.Label(
            parent,
            text="以下の文字列は手術名から削除されます",
            font=("Arial", self.font_size - 1),
            anchor="w",
        )
        description.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.surgery_listbox = self._create_listbox_with_scrollbar(parent)

        for string in self.surgery_strings_to_remove:
            self.surgery_listbox.insert(tk.END, string)

        self._create_action_buttons(
            parent,
            lambda: self._add_item(self.surgery_listbox, self.surgery_strings_to_remove, "削除文字列"),
            lambda: self._edit_item(self.surgery_listbox, self.surgery_strings_to_remove, "削除文字列"),
            lambda: self._delete_item(self.surgery_listbox, self.surgery_strings_to_remove),
        )

    def _add_item(self, listbox: tk.Listbox, item_list: list[str], item_name: str) -> None:
        dialog = tk.Toplevel(self.dialog)
        dialog.title(f"{item_name}追加")
        dialog.transient(self.dialog)
        dialog.grab_set()

        label = tk.Label(dialog, text=f"{item_name}を入力してください:", font=("Arial", self.font_size))
        label.pack(padx=20, pady=(20, 5))

        entry = tk.Entry(dialog, font=("Arial", self.font_size), width=40)
        entry.pack(padx=20, pady=5)
        entry.focus_set()

        def on_ok() -> None:
            value = entry.get().strip()
            if value:
                item_list.append(value)
                listbox.insert(tk.END, value)
                dialog.destroy()
            else:
                messagebox.showwarning("警告", f"{item_name}を入力してください", parent=dialog)

        def on_cancel() -> None:
            dialog.destroy()

        entry.bind("<Return>", lambda e: on_ok())
        entry.bind("<Escape>", lambda e: on_cancel())

        button_frame = tk.Frame(dialog)
        button_frame.pack(padx=20, pady=(5, 20))

        ok_button = tk.Button(button_frame, text="OK", command=on_ok, font=("Arial", self.font_size), width=10)
        ok_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(button_frame, text="キャンセル", command=on_cancel, font=("Arial", self.font_size), width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)

        dialog.geometry("450x150")
        self._center_window_on_parent(dialog, self.dialog)

    def _edit_item(self, listbox: tk.Listbox, item_list: list[str], item_name: str) -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "編集する項目を選択してください", parent=self.dialog)
            return

        index = selection[0]
        current_value = item_list[index]

        dialog = tk.Toplevel(self.dialog)
        dialog.title(f"{item_name}編集")
        dialog.transient(self.dialog)
        dialog.grab_set()

        label = tk.Label(dialog, text=f"{item_name}を編集してください:", font=("Arial", self.font_size))
        label.pack(padx=20, pady=(20, 5))

        entry = tk.Entry(dialog, font=("Arial", self.font_size), width=40)
        entry.insert(0, current_value)
        entry.pack(padx=20, pady=5)
        entry.focus_set()
        entry.select_range(0, tk.END)

        def on_ok() -> None:
            value = entry.get().strip()
            if value:
                item_list[index] = value
                listbox.delete(index)
                listbox.insert(index, value)
                listbox.selection_set(index)
                dialog.destroy()
            else:
                messagebox.showwarning("警告", f"{item_name}を入力してください", parent=dialog)

        def on_cancel() -> None:
            dialog.destroy()

        entry.bind("<Return>", lambda e: on_ok())
        entry.bind("<Escape>", lambda e: on_cancel())

        button_frame = tk.Frame(dialog)
        button_frame.pack(padx=20, pady=(5, 20))

        ok_button = tk.Button(button_frame, text="OK", command=on_ok, font=("Arial", self.font_size), width=10)
        ok_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(button_frame, text="キャンセル", command=on_cancel, font=("Arial", self.font_size), width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)

        dialog.geometry("450x150")
        self._center_window_on_parent(dialog, self.dialog)

    def _delete_item(self, listbox: tk.Listbox, item_list: list[str]) -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除する項目を選択してください", parent=self.dialog)
            return

        index = selection[0]
        item_value = item_list[index]

        if messagebox.askyesno("確認", f"「{item_value}」を削除しますか?", parent=self.dialog):
            item_list.pop(index)
            listbox.delete(index)

    def _save(self) -> None:
        self.result = {
            'exclusion_line_keywords': self.exclusion_line_keywords,
            'surgery_strings_to_remove': self.surgery_strings_to_remove,
        }
        self.dialog.destroy()
