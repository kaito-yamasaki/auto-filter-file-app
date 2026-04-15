# auto-filter-file-app
ファイル自動仕分けアプリ

## ルール

- 通常ルール: キーワードを含むファイル名を仕分け
- 拡張子ルール: `ext:pdf` のように指定すると拡張子一致で仕分け
- 文字比較: 全角/半角を吸収して判定

## ログ

- 既定で `logs/sort_log.csv` を出力
- 出力項目: `datetime, filename, folder, user, status, message`

`rules.json` で以下の設定が可能です。

- `log_dir` (例: `logs`)
- `log_file` (例: `sort_log.csv`)
- `user_name` (未指定時はOSユーザー名)
