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
    df_processed['日付'] = pd.to_datetime(df_processed['日付']).dt.strftime('%Y/%m/%d')

    # CSVファイルとして出力（BOM付きUTF-8）
    df_processed.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"処理が完了しました。")
    print(f"入力: {input_path} (シート: {sheet_name})")
    print(f"出力: {output_path}")
    print(f"処理件数: {len(df_processed)}件")


if __name__ == '__main__':
    # ファイルパスを指定
    input_path = r'C:\Shinseikai\OPHChecker\input\手術予定表.xls'
    output_path = r'C:\Shinseikai\OPHChecker\processed_surgery_schedule.csv'

    # 処理を実行
    process_surgery_schedule(input_path, output_path)