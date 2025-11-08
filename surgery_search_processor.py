import pandas as pd


def process_eye_surgery_data(input_file_path: str, output_file_path: str) -> None:
    """
    眼科システム手術検索のCSVファイルを処理

    Args:
        input_file_path: 入力ファイルのパス
        output_file_path: 出力ファイルのパス
    """
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

    # 麻酔の値を変換
    anesthesia_mapping = {
        '球後麻酔': '局所',
        '局所麻酔': '局所',
        '点眼麻酔': '局所',
        '全身麻酔': '全身',
        '結膜下': '局所',
    }
    df_processed['麻酔'] = df_processed['麻酔'].map(
        lambda x: anesthesia_mapping.get(x, x) if pd.notna(x) else x
    )

    # 入外の値を変換
    inpatient_mapping = {
        'あやめ': '入院',
        'わかば': '入院',
        'さくら': '入院',
        '外来': '外来'
    }
    df_processed['入外'] = df_processed['入外'].map(
        lambda x: inpatient_mapping.get(x, x) if pd.notna(x) else x
    )

    # CSVファイルに保存
    df_processed.to_csv(output_file_path, index=False, encoding='cp932')

    print(f'処理完了: {output_file_path}')

if __name__ == '__main__':
    input_path = r'C:\Shinseikai\OPHChecker\input\眼科システム手術検索.csv'
    output_path = r'C:\Shinseikai\OPHChecker\processed_surgery_search.csv'

    process_eye_surgery_data(input_path, output_path)