import pandas as pd


def compare_surgery_data(
    search_csv_path: str,
    schedule_csv_path: str,
    output_csv_path: str
) -> None:
    """
    手術検索データと手術予定表を比較してCSV形式で出力する

    Args:
        search_csv_path: 手術検索データのCSVファイルパス（基準データ）
        schedule_csv_path: 手術予定表のCSVファイルパス（比較対象データ）
        output_csv_path: 比較結果を出力するCSVファイルパス
    """
    # CSVファイルを読み込み
    df_search = pd.read_csv(search_csv_path, encoding='cp932')
    df_schedule = pd.read_csv(schedule_csv_path, encoding='cp932')

    # 手術日を統一フォーマット（YYYY/MM/DD）に変換
    df_search['手術日'] = pd.to_datetime(df_search['手術日'], format='%y/%m/%d').dt.strftime('%Y/%m/%d')
    df_schedule['手術日'] = pd.to_datetime(df_schedule['手術日']).dt.strftime('%Y/%m/%d')

    # 患者IDを文字列型に統一
    df_search['患者ID'] = df_search['患者ID'].astype(str)
    df_schedule['患者ID'] = df_schedule['患者ID'].astype(str)

    # 手術日と患者IDをキーとして左結合（left join）
    df_merged = df_search.merge(
        df_schedule,
        on=['手術日', '患者ID'],
        how='left',
        suffixes=('_検索', '_予定')
    )

    # 比較対象の列名
    compare_columns = ['入外', '術眼', '手術', '医師', '麻酔']

    # 手術日の比較列を追加（常にTrueになるはずだが、念のため）
    df_merged['手術日_比較'] = True

    # 各列の比較結果を格納
    for column in compare_columns:
        search_col = f'{column}_検索'
        schedule_col = f'{column}_予定'
        result_col = f'{column}_比較'

        # 比較結果を計算
        df_merged[result_col] = df_merged.apply(
            lambda row: '未入力' if pd.isna(row[schedule_col])
                        else (row[search_col] == row[schedule_col]),
            axis=1
        )

    # 出力用のデータフレームを作成
    # 最初の9列：検索データの元データ
    output_columns = [
        '手術日', '患者ID', '氏名_検索', '入外_検索', '術眼_検索',
        '手術_検索', '医師_検索', '麻酔_検索', '術前'
    ]

    # 次の6列：比較結果
    comparison_columns = [
        '手術日_比較', '入外_比較', '術眼_比較',
        '手術_比較', '医師_比較', '麻酔_比較'
    ]

    # 列名を元の名前に戻す（_検索を削除）
    df_output = df_merged[output_columns + comparison_columns].copy()
    df_output.columns = [
        '手術日', '患者ID', '氏名', '入外', '術眼',
        '手術', '医師', '麻酔', '術前',
        '手術日_比較', '入外_比較', '術眼_比較',
        '手術_比較', '医師_比較', '麻酔_比較'
    ]

    # CSVファイルとして保存
    df_output.to_csv(output_csv_path, index=False, encoding='cp932')

    # 統計情報を表示
    total_rows = len(df_output)
    unmatched_rows = 0

    for col in ['入外_比較', '術眼_比較', '手術_比較', '医師_比較', '麻酔_比較']:
        false_count = (df_output[col] == False).sum()
        not_entered_count = (df_output[col] == '未入力').sum()

        if false_count > 0 or not_entered_count > 0:
            unmatched_rows += 1
            print(f"{col}: 不一致={false_count}件, 未入力={not_entered_count}件")

    print(f"\n処理が完了しました。")
    print(f"総件数: {total_rows}件")
    print(f"出力ファイル: {output_csv_path}")


if __name__ == '__main__':
    # ファイルパスを指定
    search_csv_path = r'C:\Shinseikai\OPHChecker\processed_surgery_search.csv'
    schedule_csv_path = r'C:\Shinseikai\OPHChecker\processed_surgery_schedule.csv'
    output_csv_path = r'C:\Shinseikai\OPHChecker\comparison_result.csv'

    # 比較処理を実行
    compare_surgery_data(search_csv_path, schedule_csv_path, output_csv_path)