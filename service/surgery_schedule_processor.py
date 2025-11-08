import unicodedata

import pandas as pd


def process_surgery_schedule(input_path: str, output_path: str, sheet_name: str = '南館2') -> None:
    """
    手術予定表を処理してCSV形式で出力する

    Args:
        input_path: 入力Excelファイルのパス
        output_path: 出力CSVファイルのパス
        sheet_name: 処理対象のシート名（デフォルト: '南館2'）
    """
    # Excelファイルを読み込み（0行目は削除、1行目をヘッダーとして使用）
    df = pd.read_excel(input_path, sheet_name=sheet_name, header=1)

    # 必要な列を選択して並び替え
    required_columns = ['日付', 'ID', '氏名', '入外', '術式', '麻酔', '術者']
    df_processed = df[required_columns].copy()

    # 日付列を文字列形式に変換（YYYY/MM/DD形式）
    df_processed.loc[:, '日付'] = pd.to_datetime(df_processed['日付']).dt.strftime('%Y/%m/%d')  # type: ignore

    # 術式列の値を全角カナに変換
    df_processed.loc[:, '術式'] = df_processed['術式'].apply(  # type: ignore
        lambda x: unicodedata.normalize('NFKC', str(x)) if pd.notna(x) else x
    )

    # CSVファイルとして保存
    df_processed.to_csv(output_path, index=False, encoding='cp932')

    print(f"処理が完了しました。")


if __name__ == '__main__':
    # ファイルパスを指定
    input_path = r'C:\Shinseikai\OPHChecker\input\手術予定表.xls'
    output_path = r'C:\Shinseikai\OPHChecker\processed_surgery_schedule.csv'

    # 処理を実行
    process_surgery_schedule(input_path, output_path)