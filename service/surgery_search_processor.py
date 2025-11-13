import unicodedata

import pandas as pd

from utils.config_manager import (
    get_exclusion_line_keywords,
    get_paths,
    get_replacement_dict,
    get_surgery_strings_to_remove,
    load_config,
)


def process_eye_surgery_data(input_file_path: str, output_file_path: str) -> None:
    """
    手術検索データのCSVファイルを処理

    Args:
        input_file_path: 入力ファイルのパス
        output_file_path: 出力ファイルのパス
    """
    config = load_config()

    # CSVファイルを読み込み
    df = pd.read_csv(input_file_path, encoding='cp932')

    required_columns = [
        '手術日',
        '患者ID',
        '氏名',
        '手術',
        '医師',
        '麻酔',
        '病名',
        '入外',
        '右',
        '左',
        '術前'
    ]

    df_processed = df[required_columns].copy()

    # 手術日をYYYY/MM/DD形式に変換
    df_processed['手術日'] = pd.to_datetime(df_processed['手術日'], format='%y/%m/%d').dt.strftime('%Y/%m/%d')

    # 麻酔の値を変換
    anesthesia_replacements = get_replacement_dict(config, 'Replacements', 'anesthesia_replacements')
    df_processed['麻酔'] = df_processed['麻酔'].map(
        lambda x: anesthesia_replacements.get(x, x) if pd.notna(x) else x
    )

    # 術者を名字に変換
    surgeon_replacements = get_replacement_dict(config, 'Replacements', 'surgeon_replacements')
    df_processed['医師'] = df_processed['医師'].replace(surgeon_replacements)

    # 入外の値を変換
    inpatient_replacements = get_replacement_dict(config, 'Replacements', 'inpatient_replacements')
    df_processed['入外'] = df_processed['入外'].map(
        lambda x: inpatient_replacements.get(x, x) if pd.notna(x) else x
    )

    # 手術列から特定の文字列を削除
    surgery_strings_to_remove = get_surgery_strings_to_remove(config)
    for string in surgery_strings_to_remove:
        df_processed['手術'] = df_processed['手術'].str.replace(string, '', regex=False)

    # 氏名列または手術列で特定の文字列が含まれている行を削除
    exclusion_line_keywords = get_exclusion_line_keywords(config)

    columns_to_filter = ['氏名','手術']

    for column in columns_to_filter:
        for keyword in exclusion_line_keywords:
            df_processed = df_processed[~df_processed[column].str.contains(keyword, na=False)]

    # 手術列の値を全角カナに変換
    df_processed['手術'] = df_processed['手術'].apply(
        lambda x: unicodedata.normalize('NFKC', x) if pd.notna(x) else x
    )

    # 術眼列を作成
    df_processed['術眼'] = df_processed.apply(
        lambda row: 'B' if row['右'] == '○' and row['左'] == '○'
                    else 'R' if row['右'] == '○'
                    else 'L' if row['左'] == '○'
                    else '', axis=1
    )

    # 手術日と患者IDで重複を特定
    df_processed['重複'] = df_processed.duplicated(subset=['手術日', '患者ID'], keep=False)

    # 重複している行の術眼をBに変更
    df_processed.loc[df_processed['重複'], '術眼'] = 'B'

    # 重複していて、かつ左列だけに○がある行を削除
    df_processed = df_processed[~((df_processed['重複']) & (df_processed['右'] != '○') & (df_processed['左'] == '○'))]

    # 重複列を削除
    df_processed = df_processed.drop(columns=['重複', '右', '左'])

    # 列の順番を並び替え
    column_order = ['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔', '術前']
    df_processed = df_processed[column_order]

    # 手術日と患者IDで昇順にソート
    df_processed = df_processed.sort_values(by=['手術日', '患者ID'])

    # CSVファイルに保存
    df_processed.to_csv(output_file_path, index=False, encoding='cp932')

if __name__ == '__main__':
    config = load_config()
    paths = get_paths(config)

    surgery_search_data = paths['surgery_search_data']
    processed_surgery_search_data = paths['processed_surgery_search_data']

    process_eye_surgery_data(surgery_search_data, processed_surgery_search_data)
