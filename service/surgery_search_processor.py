import configparser
import logging
import unicodedata
from typing import cast

import pandas as pd

from utils.config_manager import (
    get_exclusion_line_keywords,
    get_paths,
    get_replacement_dict,
    get_surgery_strings_to_remove,
    load_config,
)


def _determine_eye_side(row: pd.Series) -> str:
    """右眼・左眼の記号から術眼を判定"""
    has_right = row['右'] == '○'
    has_left = row['左'] == '○'

    if has_right and has_left:
        return 'B'
    elif has_right:
        return 'R'
    elif has_left:
        return 'L'
    else:
        return ''


def _select_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """必要な列を選択"""
    required_columns = [
        '手術日', '患者ID', '氏名', '手術', '医師',
        '麻酔', '病名', '入外', '右', '左', '術前'
    ]
    result = df[required_columns].copy()
    if not isinstance(result, pd.DataFrame):
        raise TypeError('Expected DataFrame')
    return result


def _convert_surgery_date_format(df: pd.DataFrame) -> pd.DataFrame:
    """手術日をYYYY/MM/DD形式に変換"""
    df['手術日'] = pd.to_datetime(df['手術日'], format='%y/%m/%d').dt.strftime('%Y/%m/%d').astype(str)
    return df


def _apply_replacements(df: pd.DataFrame, config: configparser.ConfigParser) -> pd.DataFrame:
    """麻酔、術者、入外の値を置換"""
    anesthesia_replacements = get_replacement_dict(config, 'Replacements', 'anesthesia_replacements')
    df['麻酔'] = df['麻酔'].map(
        lambda x: anesthesia_replacements.get(x, x) if pd.notna(x) else x
    )

    surgeon_replacements = get_replacement_dict(config, 'Replacements', 'surgeon_replacements')
    df['医師'] = df['医師'].replace(surgeon_replacements)

    inpatient_replacements = get_replacement_dict(config, 'Replacements', 'inpatient_replacements')
    df['入外'] = df['入外'].map(
        lambda x: inpatient_replacements.get(x, x) if pd.notna(x) else x
    )

    return df


def _remove_surgery_strings(df: pd.DataFrame, config: configparser.ConfigParser) -> pd.DataFrame:
    """手術列から特定の文字列を削除"""
    surgery_strings_to_remove = get_surgery_strings_to_remove(config)
    for string in surgery_strings_to_remove:
        df['手術'] = df['手術'].str.replace(string, '', regex=False)
    return df


def _filter_exclusion_keywords(df: pd.DataFrame, config: configparser.ConfigParser) -> pd.DataFrame:
    """氏名列または手術列で特定の文字列が含まれている行を削除"""
    exclusion_line_keywords = get_exclusion_line_keywords(config)
    columns_to_filter = ['氏名', '手術']

    for column in columns_to_filter:
        for keyword in exclusion_line_keywords:
            result = df[~df[column].str.contains(keyword, na=False)]
            if isinstance(result, pd.DataFrame):
                df = result

    return df


def _normalize_surgery_text(df: pd.DataFrame) -> pd.DataFrame:
    """手術列の値を全角カナに変換"""
    df['手術'] = df['手術'].apply(
        lambda x: unicodedata.normalize('NFKC', x) if pd.notna(x) else x
    )
    return df


def _create_eye_side_column(df: pd.DataFrame) -> pd.DataFrame:
    """術眼列を作成"""
    df['術眼'] = df.apply(_determine_eye_side, axis=1)
    return df


def _handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """重複レコードを処理"""
    # 手術日と患者IDで重複を特定
    df['重複'] = df.duplicated(subset=['手術日', '患者ID'], keep=False)

    # 重複している行の術眼をBに変更
    df.loc[df['重複'], '術眼'] = 'B'

    # 重複していて、かつ左列だけに○がある行を削除
    result = df[~((df['重複']) & (df['右'] != '○') & (df['左'] == '○'))]
    if isinstance(result, pd.DataFrame):
        df = result

    # 重複列を削除
    df = df.drop(columns=['重複', '右', '左'])

    return df


def _reorder_and_sort(df: pd.DataFrame) -> pd.DataFrame:
    """列の順番を並び替えてソート"""
    column_order = ['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔', '術前']
    df = cast(pd.DataFrame, df[column_order])
    df = cast(pd.DataFrame, df.sort_values(by=['手術日', '患者ID']))
    return df


def process_eye_surgery_data(input_file_path: str, output_file_path: str) -> None:
    """
    手術検索データのCSVファイルを処理

    Args:
        input_file_path: 入力ファイルのパス
        output_file_path: 出力ファイルのパス
    """
    config = load_config()
    df = pd.read_csv(input_file_path, encoding='cp932')

    df_processed = _select_required_columns(df)
    df_processed = _convert_surgery_date_format(df_processed)
    df_processed = _apply_replacements(df_processed, config)
    df_processed = _remove_surgery_strings(df_processed, config)
    df_processed = _filter_exclusion_keywords(df_processed, config)
    df_processed = _normalize_surgery_text(df_processed)
    df_processed = _create_eye_side_column(df_processed)
    df_processed = _handle_duplicates(df_processed)
    df_processed = _reorder_and_sort(df_processed)

    df_processed.to_csv(output_file_path, index=False, encoding='cp932')
    logging.info(f"手術検索データの処理が完了しました: {output_file_path}")

if __name__ == '__main__':
    config = load_config()
    paths = get_paths(config)

    surgery_search_data = paths['surgery_search_data']
    processed_surgery_search_data = paths['processed_surgery_search_data']

    process_eye_surgery_data(surgery_search_data, processed_surgery_search_data)
