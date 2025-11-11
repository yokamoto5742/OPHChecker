import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext

from app import __version__
from service.surgery_comparator import compare_surgery_data
from service.surgery_schedule_processor import process_surgery_schedule
from service.surgery_search_processor import process_eye_surgery_data
from utils.config_manager import (
    get_appearance_settings,
    get_config_path,
    get_paths,
    load_config,
)


class OPHCheckerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"OPHChecker v{__version__}")
        self.config = load_config()
        self._apply_appearance_settings()
        self._setup_ui()

    def _apply_appearance_settings(self) -> None:
        appearance = get_appearance_settings(self.config)
        window_width = appearance['window_width']
        window_height = appearance['window_height']
        self.root.geometry(f"{window_width}x{window_height}")
        self.font_size = appearance['font_size']

    def _setup_ui(self) -> None:
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Button frame
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.start_button = tk.Button(
            button_frame,
            text="分析開始",
            command=self._start_analysis,
            font=("Arial", self.font_size + 1),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
            width=15,
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.settings_button = tk.Button(
            button_frame,
            text="設定",
            command=self._open_settings,
            font=("Arial", self.font_size + 1),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=10,
            width=15,
        )
        self.settings_button.pack(side=tk.LEFT, padx=5)

        # Status/Log display
        log_label = tk.Label(self.root, text="実行ログ:", font=("Arial", self.font_size - 1))
        log_label.grid(row=2, column=0, columnspan=2, sticky="nw", padx=10, pady=(5, 0))

        self.log_text = scrolledtext.ScrolledText(
            self.root, height=15, width=70, font=("Courier", self.font_size - 2)
        )
        self.log_text.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.root.grid_rowconfigure(3, weight=1)

        # Status bar
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor="w",
            font=("Arial", self.font_size - 2),
        )
        status_bar.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    def _log_message(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def _start_analysis(self) -> None:
        if not self._validate_config():
            return

        self.start_button.config(state=tk.DISABLED)
        self.settings_button.config(state=tk.DISABLED)
        self.log_text.delete("1.0", tk.END)
        self.status_var.set("分析中...")

        thread = threading.Thread(target=self._run_analysis, daemon=True)
        thread.start()

    def _validate_config(self) -> bool:
        paths = get_paths(self.config)
        required_paths = ["surgery_search_data", "surgery_schedule", "output_path"]

        for path_key in required_paths:
            path_value = paths.get(path_key)
            if not path_value:
                messagebox.showerror(
                    "設定エラー",
                    f"設定ファイルで '{path_key}' が設定されていません",
                )
                return False

            if not Path(path_value).exists():
                messagebox.showerror(
                    "ファイルエラー",
                    f"ファイルが見つかりません:\n{path_value}",
                )
                return False

        return True

    def _run_analysis(self) -> None:
        try:
            self._log_message("=" * 60)
            self._log_message("分析処理を開始します")
            self._log_message("=" * 60)

            # Get paths from config
            paths = get_paths(self.config)
            surgery_search_path = paths["surgery_search_data"]
            surgery_schedule_path = paths["surgery_schedule"]
            output_path = paths["output_path"]

            # Create output directory if not exists
            Path(output_path).mkdir(parents=True, exist_ok=True)

            # Process 1: Surgery Schedule
            self._log_message("\n[1/3] 手術予定表の処理を開始...")
            self.status_var.set("手術予定表を処理中...")
            schedule_output = str(Path(output_path) / "手術予定表.csv")

            try:
                process_surgery_schedule(surgery_schedule_path, schedule_output)
                self._log_message("✓ 手術予定表の処理が完了しました")
                self._log_message(f"  出力: {schedule_output}")
            except Exception as e:
                self._log_message(f"✗ エラー: {str(e)}")
                raise

            # Process 2: Eye Surgery Data
            self._log_message("\n[2/3] 眼科システムデータの処理を開始...")
            self.status_var.set("眼科システムデータを処理中...")
            search_output = str(Path(output_path) / "眼科システム手術検索.csv")

            try:
                process_eye_surgery_data(surgery_search_path, search_output)
                self._log_message("✓ 眼科システムデータの処理が完了しました")
                self._log_message(f"  出力: {search_output}")
            except Exception as e:
                self._log_message(f"✗ エラー: {str(e)}")
                raise

            # Process 3: Compare Surgery Data
            self._log_message("\n[3/3] データ比較を開始...")
            self.status_var.set("データを比較中...")
            compare_output = str(Path(output_path) / "手術データ比較結果.csv")

            try:
                compare_surgery_data(search_output, schedule_output, compare_output)
                self._log_message("✓ データ比較が完了しました")
                self._log_message(f"  出力: {compare_output}")
            except Exception as e:
                self._log_message(f"✗ エラー: {str(e)}")
                raise

            # Success
            self._log_message("\n" + "=" * 60)
            self._log_message("✓ 全ての処理が正常に完了しました")
            self._log_message("=" * 60)
            self.status_var.set("処理完了")

            # Open output folder
            self._open_output_folder(output_path)

        except Exception as e:
            self._log_message("\n" + "=" * 60)
            self._log_message(f"✗ エラーが発生しました: {str(e)}")
            self._log_message("=" * 60)
            self.status_var.set(f"エラー: {str(e)}")
            messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n\n{str(e)}")

        finally:
            self.start_button.config(state=tk.NORMAL)
            self.settings_button.config(state=tk.NORMAL)

    def _open_output_folder(self, output_path: str) -> None:
        try:
            if sys.platform == "win32":
                os.startfile(output_path)
            elif sys.platform == "darwin":
                os.system(f"open '{output_path}'")
            else:
                os.system(f"xdg-open '{output_path}'")

            self._log_message(f"出力フォルダを開きました: {output_path}")
        except Exception as e:
            self._log_message(f"✗ エラー: 出力フォルダを開けません: {str(e)}")
            messagebox.showerror(
                "エラー",
                f"出力フォルダを開けません:\n\n{str(e)}",
            )

    def _open_settings(self) -> None:
        config_path = str(get_config_path())

        try:
            if sys.platform == "win32":
                os.startfile(config_path)
            elif sys.platform == "darwin":
                os.system(f"open '{config_path}'")
            else:
                os.system(f"xdg-open '{config_path}'")

            self._log_message(f"設定ファイルを開きました: {config_path}")
            messagebox.showinfo(
                "設定",
                "設定ファイルをエディタで開きました。\n\n変更後は、このアプリケーションを再起動してください。",
            )
        except Exception as e:
            self._log_message(f"✗ エラー: 設定ファイルを開けません: {str(e)}")
            messagebox.showerror(
                "エラー",
                f"設定ファイルを開けません:\n\n{str(e)}",
            )
