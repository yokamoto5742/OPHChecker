import logging
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext
from typing import Any, Callable

import pandas as pd

from app import __version__
from service.surgery_comparator import compare_surgery_data
from service.surgery_error_extractor import surgery_error_extractor
from service.surgery_schedule_processor import process_surgery_schedule
from service.surgery_search_processor import process_eye_surgery_data
from utils.config_manager import (
    get_appearance_settings,
    get_exclusion_line_keywords,
    get_paths,
    get_replacement_dict,
    get_surgery_strings_to_remove,
    load_config,
    save_config,
    save_exclusion_line_keywords,
    save_replacement_dict,
    save_surgery_strings_to_remove,
)
from widgets.exclude_items_dialog import ExcludeItemsDialog
from widgets.replacements_dialog import ReplacementsDialog


class OPHCheckerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"OPHChecker v{__version__}")
        self.config = load_config()
        self._apply_appearance_settings()
        self._setup_ui()
        logging.info(f"OPHChecker v{__version__} を起動しました")

    def _apply_appearance_settings(self) -> None:
        appearance = get_appearance_settings(self.config)
        window_width = appearance['window_width']
        window_height = appearance['window_height']
        self.root.geometry(f"{window_width}x{window_height}")
        self.font_size = appearance['font_size']
        self.log_font_size = appearance['log_font_size']

    def _setup_ui(self) -> None:
        self.root.grid_rowconfigure(4, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        button_frame_row1 = tk.Frame(self.root)
        button_frame_row1.grid(row=1, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=10)

        button_frame_row2 = tk.Frame(self.root)
        button_frame_row2.grid(row=2, column=0, columnspan=2, pady=(5, 10), sticky="w", padx=10)

        self.start_button = tk.Button(
            button_frame_row1,
            text="分析開始",
            command=self._start_analysis,
            font=("Arial", self.font_size),
            bg="lightgreen",
            fg="black",
            padx=20,
            pady=10,
            width=15,
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.exclude_items_button = tk.Button(
            button_frame_row1,
            text="除外設定",
            command=self._open_exclude_items,
            font=("Arial", self.font_size),
            fg="black",
            padx=20,
            pady=10,
            width=15,
        )
        self.exclude_items_button.pack(side=tk.LEFT, padx=5)

        self.replacements_button = tk.Button(
            button_frame_row1,
            text="置換設定",
            command=self._open_replacements,
            font=("Arial", self.font_size),
            fg="black",
            padx=20,
            pady=10,
            width=15,
        )
        self.replacements_button.pack(side=tk.LEFT, padx=5)

        self.copy_input_path_button = tk.Button(
            button_frame_row2,
            text="入力パスコピー",
            command=self._copy_input_path_to_clipboard,
            font=("Arial", self.font_size),
            fg="black",
            padx=20,
            pady=10,
            width=15,
        )
        self.copy_input_path_button.pack(side=tk.LEFT, padx=5)

        self.close_button = tk.Button(
            button_frame_row2,
            text="閉じる",
            command=self._close_application,
            font=("Arial", self.font_size),
            fg="black",
            padx=20,
            pady=10,
            width=15,
        )
        self.close_button.pack(side=tk.LEFT, padx=5)

        log_label = tk.Label(self.root, text="実行ログ:", font=("Arial", self.font_size - 1))
        log_label.grid(row=3, column=0, columnspan=2, sticky="nw", padx=10, pady=(5, 0))

        self.log_text = scrolledtext.ScrolledText(
            self.root, height=15, width=70, font=("Courier", self.log_font_size)
        )
        self.log_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.root.grid_rowconfigure(4, weight=1)

        self.status_var = tk.StringVar(value="準備完了")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor="w",
            font=("Arial", self.font_size - 2),
        )
        status_bar.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    def _log_message(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def _start_analysis(self) -> None:
        if not self._validate_config():
            return

        self.start_button.config(state=tk.DISABLED)
        self.log_text.delete("1.0", tk.END)
        self.status_var.set("処理中...")

        thread = threading.Thread(target=self._run_analysis, daemon=True)
        thread.start()

    def _validate_config(self) -> bool:
        paths = get_paths(self.config)
        required_paths = ["surgery_search_data", "surgery_schedule", "output_path"]

        for path_key in required_paths:
            path_value = paths.get(path_key)
            if not path_value:
                logging.error(f"設定ファイルで '{path_key}' が設定されていません")
                messagebox.showerror(
                    "設定エラー",
                    f"設定ファイルで '{path_key}' が設定されていません",
                )
                return False

            if not Path(path_value).exists():
                logging.error(f"ファイルが見つかりません: {path_value}")
                messagebox.showerror(
                    "ファイルエラー",
                    f"ファイルが見つかりません:\n{path_value}",
                )
                return False

        return True

    def _execute_step(
        self,
        step_num: int,
        total_steps: int,
        step_name: str,
        func: Callable,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """処理ステップを実行"""
        self._log_message(f"\n[{step_num}/{total_steps}] {step_name}を開始...")
        logging.info(f"[{step_num}/{total_steps}] {step_name}を開始")

        try:
            result = func(*args, **kwargs)
            self._log_message(f"✓ {step_name}が完了しました")
            logging.info(f"{step_name}が完了しました")
            return result
        except Exception as e:
            self._log_message(f"✗ エラー: {str(e)}")
            logging.error(f"{step_name}中にエラーが発生: {str(e)}", exc_info=True)
            raise

    def _process_surgery_schedule(self, paths: dict) -> None:
        """手術予定表の処理"""
        self._execute_step(
            1, 4, "手術予定表の処理",
            process_surgery_schedule,
            paths['surgery_schedule'],
            paths['processed_surgery_schedule']
        )

    def _process_surgery_search(self, paths: dict) -> None:
        """眼科手術検索データの処理"""
        self._execute_step(
            2, 4, "手術検索データの処理",
            process_eye_surgery_data,
            paths['surgery_search_data'],
            paths['processed_surgery_search_data']
        )

    def _compare_surgery_data(self, paths: dict) -> None:
        """データ比較"""
        self._execute_step(
            3, 4, "データ比較",
            compare_surgery_data,
            paths['processed_surgery_search_data'],
            paths['processed_surgery_schedule'],
            paths['comparison_result']
        )

    def _extract_surgery_errors(self, paths: dict) -> str:
        """眼科手術指示確認ファイルを作成"""
        self._log_message("\n[4/4] 眼科手術指示確認ファイルを作成開始...")
        logging.info("[4/4] 眼科手術指示確認ファイルを作成開始")

        try:
            instruction_file = surgery_error_extractor(
                paths['comparison_result'],
                paths['output_path'],
                paths['template_path']
            )
            if instruction_file:
                self._log_message("✓ 眼科手術指示確認ファイルを作成しました")
                logging.info("眼科手術指示確認ファイルを作成しました")
            else:
                self._log_message("✓ 不一致および未入力データはありませんでした")
                logging.info("不一致および未入力データはありませんでした")
            return instruction_file
        except Exception as e:
            self._log_message(f"✗ エラー: {str(e)}")
            logging.error(f"眼科手術指示確認ファイルの作成中にエラーが発生: {str(e)}", exc_info=True)
            raise

    def _log_completion_summary(self, processed_surgery_search_data: str) -> None:
        """完了サマリーをログに記録"""
        df_search = pd.read_csv(processed_surgery_search_data, encoding='cp932')
        self._log_message(f"\n対象期間: {df_search['手術日'].min()} ～ {df_search['手術日'].max()}")
        logging.info(f"対象期間: {df_search['手術日'].min()} ～ {df_search['手術日'].max()}")
        self.status_var.set("処理完了")
        logging.info("すべての処理が正常に完了しました")

    def _handle_analysis_error(self, e: Exception) -> None:
        """分析エラーをハンドリング"""
        logging.error(f"分析処理中に予期しないエラーが発生: {str(e)}", exc_info=True)
        self._log_message("\n" + "=" * 60)
        self._log_message(f"✗ エラーが発生しました: {str(e)}")
        self._log_message("=" * 60)
        self.status_var.set(f"エラー: {str(e)}")
        messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n\n{str(e)}")

    def _run_analysis(self) -> None:
        try:
            logging.info("分析処理を開始します")
            self._log_message("=" * 60)
            self._log_message("分析処理を開始します")
            self._log_message("=" * 60)

            paths = get_paths(self.config)
            Path(paths["output_path"]).mkdir(parents=True, exist_ok=True)

            self._process_surgery_schedule(paths)
            self._process_surgery_search(paths)
            self._compare_surgery_data(paths)
            self._extract_surgery_errors(paths)

            self._log_completion_summary(paths['processed_surgery_search_data'])
            self._open_output_folder(paths["output_path"])

        except Exception as e:
            self._handle_analysis_error(e)

        finally:
            self.start_button.config(state=tk.NORMAL)

    def _open_output_folder(self, output_path: str) -> None:
        try:
            os.startfile(output_path)
            logging.info(f"出力フォルダを開きました: {output_path}")
        except Exception as e:
            logging.error(f"出力フォルダを開けません: {str(e)}", exc_info=True)
            self._log_message(f"✗ エラー: 出力フォルダを開けません: {str(e)}")
            messagebox.showerror(
                "エラー",
                f"出力フォルダを開けません:\n\n{str(e)}",
            )

    def _open_exclude_items(self) -> None:
        try:
            # 現在の除外項目を取得
            exclusion_line_keywords = get_exclusion_line_keywords(self.config)
            surgery_strings_to_remove = get_surgery_strings_to_remove(self.config)

            # ダイアログを表示
            dialog = ExcludeItemsDialog(
                self.root,
                exclusion_line_keywords,
                surgery_strings_to_remove,
                self.font_size,
            )
            result = dialog.show()

            # 結果が返されたら保存
            if result:
                save_exclusion_line_keywords(self.config, result['exclusion_line_keywords'])
                save_surgery_strings_to_remove(self.config, result['surgery_strings_to_remove'])
                save_config(self.config)

                logging.info("除外項目を保存しました")
                self._log_message("✓ 除外項目を保存しました")
                messagebox.showinfo("保存完了", "除外項目を保存しました", parent=self.root)
        except Exception as e:
            logging.error(f"除外項目の編集中にエラーが発生: {str(e)}", exc_info=True)
            self._log_message(f"✗ エラー: 除外項目の編集中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"除外項目の編集中にエラーが発生しました:\n\n{str(e)}", parent=self.root)


    def _open_replacements(self) -> None:
        try:
            # 現在の置換設定を取得
            anesthesia_replacements = get_replacement_dict(self.config, 'Replacements', 'anesthesia_replacements')
            surgeon_replacements = get_replacement_dict(self.config, 'Replacements', 'surgeon_replacements')
            inpatient_replacements = get_replacement_dict(self.config, 'Replacements', 'inpatient_replacements')

            # ダイアログを表示
            dialog = ReplacementsDialog(
                self.root,
                anesthesia_replacements,
                surgeon_replacements,
                inpatient_replacements,
                self.font_size,
            )
            result = dialog.show()

            # 結果が返されたら保存
            if result:
                save_replacement_dict(self.config, 'Replacements', 'anesthesia_replacements', result['anesthesia_replacements'])
                save_replacement_dict(self.config, 'Replacements', 'surgeon_replacements', result['surgeon_replacements'])
                save_replacement_dict(self.config, 'Replacements', 'inpatient_replacements', result['inpatient_replacements'])
                save_config(self.config)

                logging.info("置換設定を保存しました")
                self._log_message("✓ 置換設定を保存しました")
                messagebox.showinfo("保存完了", "置換設定を保存しました", parent=self.root)
        except Exception as e:
            logging.error(f"置換設定の編集中にエラーが発生: {str(e)}", exc_info=True)
            self._log_message(f"✗ エラー: 置換設定の編集中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"置換設定の編集中にエラーが発生しました:\n\n{str(e)}", parent=self.root)

    def _copy_input_path_to_clipboard(self) -> None:
        paths = get_paths(self.config)
        input_path = paths.get("input_path", "")

        if not input_path:
            logging.warning("入力パスが設定されていません")
            self._log_message("✗ 入力パスが設定されていません")
            messagebox.showwarning("警告", "入力パスが設定されていません")
            return

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(input_path)
            self.root.update()

            logging.info(f"入力パスをクリップボードにコピーしました: {input_path}")
            self._show_auto_close_message("コピー完了", f"入力パスをクリップボードにコピーしました:\n\n{input_path}")
        except Exception as e:
            logging.error(f"クリップボードへのコピーに失敗: {str(e)}", exc_info=True)
            self._log_message(f"✗ エラー: クリップボードへのコピーに失敗しました: {str(e)}")
            messagebox.showerror("エラー", f"クリップボードへのコピーに失敗しました:\n\n{str(e)}")

    def _show_auto_close_message(self, title: str, message: str, duration_ms: int = 1000) -> None:
        """3秒後に自動的に閉じるメッセージダイアログを表示"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()

        # ダイアログの内容
        label = tk.Label(dialog, text=message, font=("Arial", self.font_size), padx=20, pady=20)
        label.pack()

        # ウィンドウを中央に配置
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # 指定時間後に自動的に閉じる
        dialog.after(duration_ms, dialog.destroy)

    def _close_application(self) -> None:
        if self.start_button.cget("state") == tk.DISABLED:
            logging.warning("分析処理が実行中のため、アプリケーションを閉じることができません")
            messagebox.showwarning(
                "実行中",
                "分析処理が実行中です。\n処理が完了してからアプリケーションを閉じてください。",
            )
            return
        logging.info("アプリケーションを終了します")
        self.root.quit()
