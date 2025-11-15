import tkinter as tk
from abc import ABC, abstractmethod


class BaseDialog(ABC):
    def __init__(self, parent: tk.Tk, title: str, font_size: int = 11) -> None:
        self.parent = parent
        self.result = None
        self.font_size = font_size

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._setup_ui()
        self._center_window()

    @abstractmethod
    def _setup_ui(self) -> None:
        pass

    @abstractmethod
    def _save(self) -> None:
        pass

    def _cancel(self) -> None:
        self.result = None
        self.dialog.destroy()

    def _create_button_frame(self) -> None:
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

    def _create_listbox_with_scrollbar(self, parent: tk.Frame) -> tk.Listbox:
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

        return listbox

    def _create_action_buttons(self, parent: tk.Frame, add_command, edit_command, delete_command) -> None:
        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        add_button = tk.Button(
            btn_frame,
            text="追加",
            command=add_command,
            font=("Arial", self.font_size - 1),
            width=10,
        )
        add_button.pack(side=tk.LEFT, padx=2)

        edit_button = tk.Button(
            btn_frame,
            text="編集",
            command=edit_command,
            font=("Arial", self.font_size - 1),
            width=10,
        )
        edit_button.pack(side=tk.LEFT, padx=2)

        delete_button = tk.Button(
            btn_frame,
            text="削除",
            command=delete_command,
            font=("Arial", self.font_size - 1),
            width=10,
        )
        delete_button.pack(side=tk.LEFT, padx=2)

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
