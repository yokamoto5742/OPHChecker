import tkinter as tk
from tkinter import messagebox, ttk


class ReplacementsDialog:
    def __init__(self, parent: tk.Tk, anesthesia_replacements: dict[str, str],
                 surgeon_replacements: dict[str, str], inpatient_replacements: dict[str, str],
                 font_size: int = 11) -> None:
        self.parent = parent
        self.result = None
        self.font_size = font_size

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("置換設定編集")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.anesthesia_replacements = anesthesia_replacements.copy()
        self.surgeon_replacements = surgeon_replacements.copy()
        self.inpatient_replacements = inpatient_replacements.copy()

        self._setup_ui()
        self._center_window()

    def _setup_ui(self) -> None:
        # タブ作成
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # タブ1: 麻酔方法置換
        anesthesia_frame = tk.Frame(notebook)
        notebook.add(anesthesia_frame, text="麻酔方法置換")
        self._setup_replacements_tab(anesthesia_frame, self.anesthesia_replacements, "anesthesia")

        # タブ2: 執刀医置換
        surgeon_frame = tk.Frame(notebook)
        notebook.add(surgeon_frame, text="執刀医置換")
        self._setup_replacements_tab(surgeon_frame, self.surgeon_replacements, "surgeon")

        # タブ3: 入院区分置換
        inpatient_frame = tk.Frame(notebook)
        notebook.add(inpatient_frame, text="入院区分置換")
        self._setup_replacements_tab(inpatient_frame, self.inpatient_replacements, "inpatient")

        # ボタンフレーム
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        save_button = tk.Button(
            button_frame,
            text="保存",
            command=self._save,
            font=("Arial", self.font_size),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5,
            width=10,
        )
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(
            button_frame,
            text="キャンセル",
            command=self._cancel,
            font=("Arial", self.font_size),
            bg="#f44336",
            fg="white",
            padx=20,
            pady=5,
            width=10,
        )
        cancel_button.pack(side=tk.LEFT, padx=5)

    def _setup_replacements_tab(self, parent: tk.Frame, replacements_dict: dict[str, str], tab_type: str) -> None:
        # 説明ラベル
        description = tk.Label(
            parent,
            text="置換前の値 → 置換後の値",
            font=("Arial", self.font_size - 1),
            anchor="w",
        )
        description.pack(fill=tk.X, padx=10, pady=(10, 5))

        # リストボックスとスクロールバー
        list_frame = tk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(
            list_frame,
            font=("Arial", self.font_size),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # リストボックスにデータを追加
        for key, value in replacements_dict.items():
            listbox.insert(tk.END, f"{key} → {value}")

        # リストボックスを保存
        if tab_type == "anesthesia":
            self.anesthesia_listbox = listbox
        elif tab_type == "surgeon":
            self.surgeon_listbox = listbox
        elif tab_type == "inpatient":
            self.inpatient_listbox = listbox

        # ボタンフレーム
        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        add_button = tk.Button(
            btn_frame,
            text="追加",
            command=lambda: self._add_replacement(listbox, replacements_dict),
            font=("Arial", self.font_size - 1),
            width=10,
        )
        add_button.pack(side=tk.LEFT, padx=2)

        edit_button = tk.Button(
            btn_frame,
            text="編集",
            command=lambda: self._edit_replacement(listbox, replacements_dict),
            font=("Arial", self.font_size - 1),
            width=10,
        )
        edit_button.pack(side=tk.LEFT, padx=2)

        delete_button = tk.Button(
            btn_frame,
            text="削除",
            command=lambda: self._delete_replacement(listbox, replacements_dict),
            font=("Arial", self.font_size - 1),
            width=10,
        )
        delete_button.pack(side=tk.LEFT, padx=2)

    def _add_replacement(self, listbox: tk.Listbox, replacements_dict: dict[str, str]) -> None:
        dialog = tk.Toplevel(self.dialog)
        dialog.title("置換追加")
        dialog.transient(self.dialog)
        dialog.grab_set()

        # 置換前
        label1 = tk.Label(dialog, text="置換前の値:", font=("Arial", self.font_size))
        label1.pack(padx=20, pady=(20, 5))

        entry_key = tk.Entry(dialog, font=("Arial", self.font_size), width=40)
        entry_key.pack(padx=20, pady=5)
        entry_key.focus_set()

        # 置換後
        label2 = tk.Label(dialog, text="置換後の値:", font=("Arial", self.font_size))
        label2.pack(padx=20, pady=(10, 5))

        entry_value = tk.Entry(dialog, font=("Arial", self.font_size), width=40)
        entry_value.pack(padx=20, pady=5)

        def on_ok() -> None:
            key = entry_key.get().strip()
            value = entry_value.get().strip()
            if key and value:
                if key in replacements_dict:
                    messagebox.showwarning("警告", "同じ置換前の値が既に存在します", parent=dialog)
                    return
                replacements_dict[key] = value
                listbox.insert(tk.END, f"{key} → {value}")
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "置換前と置換後の値を入力してください", parent=dialog)

        def on_cancel() -> None:
            dialog.destroy()

        entry_value.bind("<Return>", lambda e: on_ok())
        entry_value.bind("<Escape>", lambda e: on_cancel())

        button_frame = tk.Frame(dialog)
        button_frame.pack(padx=20, pady=(5, 20))

        ok_button = tk.Button(button_frame, text="OK", command=on_ok, font=("Arial", self.font_size), width=10)
        ok_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(button_frame, text="キャンセル", command=on_cancel, font=("Arial", self.font_size), width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)

        dialog.geometry("450x200")
        self._center_window_on_parent(dialog, self.dialog)

    def _edit_replacement(self, listbox: tk.Listbox, replacements_dict: dict[str, str]) -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "編集する項目を選択してください", parent=self.dialog)
            return

        index = selection[0]
        current_text = listbox.get(index)

        # "キー → 値" の形式から分割
        parts = current_text.split(" → ")
        if len(parts) != 2:
            messagebox.showerror("エラー", "データ形式が正しくありません", parent=self.dialog)
            return

        current_key = parts[0]
        current_value = parts[1]

        dialog = tk.Toplevel(self.dialog)
        dialog.title("置換編集")
        dialog.transient(self.dialog)
        dialog.grab_set()

        # 置換前
        label1 = tk.Label(dialog, text="置換前の値:", font=("Arial", self.font_size))
        label1.pack(padx=20, pady=(20, 5))

        entry_key = tk.Entry(dialog, font=("Arial", self.font_size), width=40)
        entry_key.insert(0, current_key)
        entry_key.pack(padx=20, pady=5)
        entry_key.focus_set()
        entry_key.select_range(0, tk.END)

        # 置換後
        label2 = tk.Label(dialog, text="置換後の値:", font=("Arial", self.font_size))
        label2.pack(padx=20, pady=(10, 5))

        entry_value = tk.Entry(dialog, font=("Arial", self.font_size), width=40)
        entry_value.insert(0, current_value)
        entry_value.pack(padx=20, pady=5)

        def on_ok() -> None:
            new_key = entry_key.get().strip()
            new_value = entry_value.get().strip()
            if new_key and new_value:
                # キーが変更された場合、既存のキーとの重複をチェック
                if new_key != current_key and new_key in replacements_dict:
                    messagebox.showwarning("警告", "同じ置換前の値が既に存在します", parent=dialog)
                    return

                # 古いキーを削除
                del replacements_dict[current_key]
                # 新しいキーと値を追加
                replacements_dict[new_key] = new_value

                # リストボックスを更新
                listbox.delete(index)
                listbox.insert(index, f"{new_key} → {new_value}")
                listbox.selection_set(index)
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "置換前と置換後の値を入力してください", parent=dialog)

        def on_cancel() -> None:
            dialog.destroy()

        entry_value.bind("<Return>", lambda e: on_ok())
        entry_value.bind("<Escape>", lambda e: on_cancel())

        button_frame = tk.Frame(dialog)
        button_frame.pack(padx=20, pady=(5, 20))

        ok_button = tk.Button(button_frame, text="OK", command=on_ok, font=("Arial", self.font_size), width=10)
        ok_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(button_frame, text="キャンセル", command=on_cancel, font=("Arial", self.font_size), width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)

        dialog.geometry("450x200")
        self._center_window_on_parent(dialog, self.dialog)

    def _delete_replacement(self, listbox: tk.Listbox, replacements_dict: dict[str, str]) -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除する項目を選択してください", parent=self.dialog)
            return

        index = selection[0]
        current_text = listbox.get(index)

        # "キー → 値" の形式から分割
        parts = current_text.split(" → ")
        if len(parts) != 2:
            messagebox.showerror("エラー", "データ形式が正しくありません", parent=self.dialog)
            return

        key = parts[0]

        if messagebox.askyesno("確認", f"「{current_text}」を削除しますか?", parent=self.dialog):
            del replacements_dict[key]
            listbox.delete(index)

    def _save(self) -> None:
        self.result = {
            'anesthesia_replacements': self.anesthesia_replacements,
            'surgeon_replacements': self.surgeon_replacements,
            'inpatient_replacements': self.inpatient_replacements,
        }
        self.dialog.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.dialog.destroy()

    def _center_window(self) -> None:
        self.dialog.update_idletasks()
        width = 600
        height = 500
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _center_window_on_parent(self, child: tk.Toplevel, parent: tk.Toplevel) -> None:
        child.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (child.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (child.winfo_height() // 2)
        child.geometry(f"+{x}+{y}")

    def show(self) -> dict | None:
        self.dialog.wait_window()
        return self.result
