# AMB Lap Speak - RCカー練習用ラップタイマー

**日本語音声読み上げ機能付き、個人練習に特化したAMB P3デコーダー対応RCカーラップタイマーシステム**

このシステムは、個々のドライバーが自身の走りを詳細に分析し、スキルアップすることを目的として設計されています。

[🇯🇵 日本語版README](README_ja.md) | [🇺🇸 English Version](README.md)

## 🎯 主な機能

- 🚗 **練習走行に最適化された画面**: コントロールラインを通過したマシンが常に一番上に表示されます。
- 📈 **詳細な走行分析**: マシンごとにベストラップ、過去10周の移動平均タイム、ラップタイムの標準偏差をリアルタイムで表示し、安定性を把握できます。
- 📊 **ラップタイムの可視化**: ポンダー番号をクリックすると、ラップタイムの推移を示すグラフ付きの詳細ページに移動します。
- 🗣️ **ポンダーごとの音声読み上げ**: 特定のマシンのみラップタイムを読み上げさせることができ、聞きたい情報に集中できます。
- 🏷️ **カスタムニックネーム**: 音声読み上げ用のカスタムニックネームを設定し、複数台走行時の識別を容易にします。
- 🇯🇵 **日本語インターフェース**: 完全日本語化されたWebインターフェースと、音声読み上げに最適化された時間フォーマット。
- ⏱️ **リアルタイム計測**: AMB P3デコーダーに接続し、通過するポンダーを瞬時に捉えます。
- 🗄️ **データ保存**: 全てのラップデータはMySQLデータベースに保存され、後から分析することが可能です。
- 🚀 **高性能バックエンド**: アプリケーションのデータをメモリ上に保持することで、1秒ごとに更新される高速なWebインターフェースを実現しています。
- 📱 **レスポンシブデザイン**: サーキットサイドでも見やすい、クリーンでモバイルフレンドリーなデザインです。

## 🖥️ Webインターフェース

### メインダッシュボード
一目で状況がわかるように設計されています。
- 最新の通過記録でソートされるため、最後にラインを通過したマシンが常に最上部に表示されます。
- 各マシンについて、重要なパフォーマンス指標が表示されます:
  - **ポンダー**: トランスポンダーID。クリックすると詳細な履歴ページに移動します。
  - **ニックネーム**: 音声読み上げ用のカスタム名（未設定の場合は「-」）。
  - **ベストラップ**: サーバー起動後の最速ラップ。
  - **平均(10周)**: 直近10周の移動平均タイム。
  - **標準偏差**: ラップタイムの標準偏差。タイムのばらつき（安定性）を示します。
  - **最新ラップ**: 直前に計測されたラップタイム。
  - **最終通過**: 最後にコントロールラインを通過した時刻。
  - **アナウンス**: そのマシンの音声読み上げを有効/無効にするチェックボックス。

### ラップ履歴ページ
- メインダッシュボードでポンダー番号をクリックすると表示されます。
- **ニックネーム設定**: 音声読み上げ用のカスタム名を設定する入力フィールド。
- **統計サマリー**: 総周回数、ベストラップ、直近10周の平均ラップを表示します。
- **ラップタイムチャート**: 全てのラップタイムを折れ線グラフで表示し、タイムの傾向やばらつきを視覚的に確認できます。
- **全ラップデータ**: 全てのラップについて、周回数、ラップタイム、計測時刻を一覧で表示します。

## 🎤 音声読み上げ機能
- メインダッシュボードのチェックボックスで、マシンごとに個別に音声読み上げのON/OFFを切り替えられます。
- ラップ履歴ページで各マシンにカスタムニックネームを設定し、複数台走行時の識別を容易にできます。
- 有効にすると、ニックネーム（または未設定時はトランスポンダーID）とラップタイムを日本語フォーマットで読み上げます。
- **読み上げ例**: 
  - ニックネームあり: 「１番、65秒24」（読み方：いちばん、ろくじゅうごびょう にーよん）
  - ニックネームなし: 「4000822、65秒24」（読み方：よんひゃくまん はっぴゃく にじゅうに、ろくじゅうごびょう にーよん）
- 時間フォーマットは日本語読み上げ用に最適化され、「65.24」を「65秒24」として明確な数字認識を可能にします。

## 📋 システム要件

- **Python**: 3.7以上
- **データベース**: MySQL 5.7以上 または Docker
- **ハードウェア**: AMB P3デコーダー（ネットワーク接続対応）
- **ブラウザ**: モダンWebブラウザ
- **音声出力**: スピーカーまたはヘッドフォン

## 🚀 クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/hama-jp/AMB_Lap_Speak.git
cd AMB_Lap_Speak
```

### 2. 自動セットアップ（推奨）

```bash
# セットアップスクリプトを実行
chmod +x setup.sh
./setup.sh
```

### 3. 手動セットアップ

#### Python環境のセットアップ

```bash
# uv のインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成
uv venv

# 仮想環境の有効化
source .venv/bin/activate

# 依存関係のインストール
uv pip install -r requirements.txt
```

#### MySQLデータベースのセットアップ

**Docker使用（推奨）:**

```bash
# MySQL コンテナの起動
docker run -d --name mysql-amb \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=karts \
  -e MYSQL_USER=kart \
  -e MYSQL_PASSWORD=karts \
  -p 3307:3306 \
  mysql:5.7

# MySQL起動待機（30秒）
sleep 30

# データベーススキーマの読み込み
cat schema | docker exec -i mysql-amb mysql -u kart -pkarts karts
```

### 4. AMBデコーダーの設定

`conf.yaml` でAMBデコーダーの設定を行います：

```yaml
---
ip: '192.168.1.21'    # AMBデコーダーのIPアドレス
port: 5403            # AMBデコーダーのポート（通常5403）
file: "/tmp/out.log"
debug_file: "/tmp/amb_raw.log"
mysql_backend: True
mysql_host: '127.0.0.1'
mysql_port: 3307      # ローカルMySQLの場合は3306
mysql_db: 'karts'
mysql_user: 'kart'
mysql_password: 'karts'
```

### 5. RCカー情報の登録（オプション）

ポンダーIDとマシン番号を紐付けて、分かりやすくすることができます。

```bash
# 仮想環境の有効化
source .venv/bin/activate

# RCカーデータの追加
python -c "
from AmbP3.write import open_mysql_connection
conn = open_mysql_connection(user='kart', db='karts', password='karts', host='127.0.0.1', port=3307)
cursor = conn.cursor()

# RCカー情報（カー番号、トランスポンダーID、ドライバー名）
cars = [
    (1, 4000822, 'マイカー1号'),
    (2, 4000823, 'マイカー2号'),
    # 必要に応じて追加
]

for car_number, transponder_id, name in cars:
    cursor.execute('INSERT IGNORE INTO cars (car_number, transponder_id, name) VALUES (%s, %s, %s)', 
                   (car_number, transponder_id, name))

conn.commit()
conn.close()
print('RCカーデータを正常に追加しました')
"
```

## 🏃‍♂️ システムの実行

### 1. AMBクライアント（データ収集）の開始

```bash
source .venv/bin/activate
python amb_client.py
```

### 2. Webインターフェースの開始

新しいターミナルで：

```bash
source .venv/bin/activate
python web_app.py
```

**Webインターフェースアクセス**: http://localhost:5000

## 🏗️ システム構成

```
AMB P3デコーダー（ハードウェア）
    ↓ TCP Socket（ポート5403）
amb_client.py（データ収集）
    ↓ プロトコルデコード
MySQL データベース（データ保存）
    ↓ Web API (起動時と新規ラップ毎)
web_app.py (Flask Webサーバー + インメモリデータストア)
    ↓ HTTP（ポート5000）
Webブラウザ（ポーリングによるライブ表示）
    ↓ 音声出力
音声読み上げ（バックエンドで新規ラップをトリガー）
```

### ファイル構成

```
AMB_Lap_Speak/
├── AmbP3/                 # コアタイミングシステムパッケージ
│   ├── ...
│   └── voice_announcer.py # 音声読み上げシステム
├── templates/            # Webインターフェーステンプレート
│   ├── index.html       # メインダッシュボード
│   └── laps.html        # ラップ履歴詳細ページ
├── amb_client.py        # メインタイミングクライアント
├── web_app.py          # Flask Webアプリケーション
├── conf.yaml           # 設定ファイル
├── schema              # MySQL データベーススキーマ
├── requirements.txt    # Python依存関係
├── setup.sh           # 自動セットアップスクリプト
├── README.md          # 英語版README
└── README_ja.md       # 日本語版README（このファイル）
```

## 📚 API リファレンス

- `GET /`: メインのダッシュボードページを返します。
- `GET /laps/<transponder_id>`: 特定ポンダーの詳細なラップ履歴ページを返します。
- `GET /api/all_laps`: アクティブな全マシンの最新ラップデータを、最終通過時刻でソートされたJSONリストで返します。メインダッシュボードで使用されます。
- `GET /api/laps/<transponder_id>`: 特定マシンの完全な履歴と統計情報を含むJSONオブジェクトを返します。ラップ履歴ページで使用されます。
- `POST /api/voice_toggle/<transponder_id>`: 特定マシンの音声読み上げ設定を切り替えます。
- `POST /api/nickname/<transponder_id>`: 特定マシンの音声読み上げ用カスタムニックネームを更新します。

## 🤝 コントリビューション

1. リポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを開く

## 📄 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。
