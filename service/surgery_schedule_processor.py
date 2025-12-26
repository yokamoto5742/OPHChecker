import logging
import unicodedata
from typing import Mapping

import pandas as pd


def process_surgery_schedule(surgery_schedule: str, processed_surgery_schedule: str, sheet_name: str = '南館2') -> None:
    """
    手術予定表を処理してCSV形式で出力

    Args:
        surgery_schedule: 入力Excelファイルのパス
        processed_surgery_schedule: 出力CSVファイルのパス
        sheet_name: 処理対象のシート名（デフォルト: '南館2'）
    """
    df = pd.read_excel(surgery_schedule, sheet_name=sheet_name, header=1)

    required_columns = ['日付', 'ID', '氏名', '入外', '術式', '麻酔', '術者']
    df_processed = df[required_columns].copy()

    date_series = df_processed['日付']
    df_processed['日付'] = pd.to_datetime(date_series).dt.strftime('%Y/%m/%d')

    # 術式列の値を全角カナに変換
    surgery_series = df_processed['術式']
    df_processed['術式'] = surgery_series.apply(
        lambda x: unicodedata.normalize('NFKC', str(x)) if pd.notna(x) else x
    )

    split_series = df_processed['術式']
    df_processed[['術眼', '手術']] = split_series.str.split(')', n=1, expand=True)
    hand_series = df_processed['手術']
    df_processed['手術'] = hand_series.str.strip()

    df_processed = df_processed.drop(columns=['術式'])

    rename_mapping: Mapping[str, str] = {'日付': '手術日', 'ID': '患者ID', '術者': '医師'}
    df_processed = df_processed.rename(columns=rename_mapping)

    df_processed = df_processed[['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔']]

    df_processed = df_processed.sort_values(by=['手術日', '患者ID'])

    df_processed.to_csv(processed_surgery_schedule, index=False, encoding='cp932')

    logging.info(f"手術予定表の処理が完了しました: {processed_surgery_schedule}")


if __name__ == '__main__':
    from utils.config_manager import load_config, get_paths

    config = load_config()
    paths = get_paths(config)

    process_surgery_schedule(
        paths['surgery_schedule'],
        paths['processed_surgery_schedule']
    )
