import unicodedata

import pandas as pd


def process_surgery_schedule(surgery_schedule: str, processed_surgery_schedule: str, sheet_name: str = '南館2') -> None:
    """
    手術予定表を処理してCSV形式で出力する

    Args:
        surgery_schedule: 入力Excelファイルのパス
        processed_surgery_schedule: 出力CSVファイルのパス
        sheet_name: 処理対象のシート名（デフォルト: '南館2'）
    """
    # Excelファイルを読み込み（0行目は削除、1行目をヘッダーとして使用）
    df = pd.read_excel(surgery_schedule, sheet_name=sheet_name, header=1)

    # 必要な列を選択して並び替え
    required_columns = ['日付', 'ID', '氏名', '入外', '術式', '麻酔', '術者']
    df_processed = df[required_columns].copy()

    # 日付列を文字列形式に変換（YYYY/MM/DD形式）
    df_processed.loc[:, '日付'] = pd.to_datetime(df_processed['日付']).dt.strftime('%Y/%m/%d')

    # 術式列の値を全角カナに変換
    df_processed.loc[:, '術式'] = df_processed['術式'].apply(
        lambda x: unicodedata.normalize('NFKC', str(x)) if pd.notna(x) else x
    )

    # 術式列を ')' で分割して術眼列と手術列を作成
    df_processed[['術眼', '手術']] = df_processed['術式'].str.split(')', n=1, expand=True)
    df_processed['手術'] = df_processed['手術'].str.strip()  # 前後の空白を削除

    # 術式列を削除
    df_processed = df_processed.drop(columns=['術式'])

    # 列名を変更
    df_processed = df_processed.rename(columns={'日付': '手術日', 'ID': '患者ID', '術者': '医師',})

    # 列の順番を並び替え
    df_processed = df_processed[['手術日', '患者ID', '氏名', '入外', '術眼', '手術', '医師', '麻酔']]

    # CSVファイルとして保存
    df_processed.to_csv(processed_surgery_schedule, index=False, encoding='cp932')

    print(f"処理が完了しました。")


if __name__ == '__main__':
    from utils.config_manager import load_config, get_paths

    config = load_config()
    paths = get_paths(config)

    process_surgery_schedule(
        paths['surgery_schedule'],
        paths['processed_surgery_schedule']
    )
