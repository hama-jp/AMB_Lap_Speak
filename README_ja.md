# AMB RC Timer - リアルタイムRCカータイミングシステム

**日本語音声読み上げ機能付きのAMB P3デコーダー対応RCカータイミングシステム**

リアルタイムでラップタイムを表示し、自然な日本語音声でレース状況を読み上げる本格的なタイミングシステムです。

## 🎯 主な機能

- 🏁 **リアルタイムラップタイミング**: AMB P3デコーダーと接続してトランスポンダーパスを追跡
- 📊 **ライブWebダッシュボード**: 最大16台のRCカーのラップタイムをリアルタイム表示
- 🗣️ **日本語音声読み上げ**: Google TTS使用による自然な日本語でのレース状況アナウンス
- 🗄️ **MySQL データベース**: 全てのタイミングデータを永続保存
- ⏱️ **自動ラップ計算**: 有効なラップのみを自動フィルタリング
- 🔄 **自動更新インターフェース**: 2秒間隔でのWebダッシュボード更新
- 📱 **レスポンシブデザイン**: モバイル端末でもサーキットサイドで使用可能
- 🏆 **レース管理**: ベストラップ、ラップ数、ドライバー順位を自動追跡

## 🎤 音声読み上げ機能

### 個別ラップアナウンス（デフォルト：シンプルモード）
- **ラップ完了時**: "1分5.234秒"（時間のみ）
- **ベストラップ更新**: "59.789秒、ベストラップ！"
- **新記録樹立**: "新記録！59.789秒"

### 詳細モード（オプション設定）
- **ラップ完了時**: "3ラップ、1分5.234秒"（ラップ数含む）
- **カー番号含む**: "カー5、3ラップ、1分5.234秒"

### 全車タイム読み上げ（デフォルト：無効）
- **自動読み上げ**: オプションで30秒間隔で全車の現在順位とタイムを自動アナウンス
- **手動読み上げ**: Webインターフェースのボタンでいつでも実行可能
- **読み上げ例**: "現在の順位、1位、5ラップ、ベスト59.8秒、2位、4ラップ、ベスト1分2.1秒..."

### 対応音声エンジン
- **Google TTS (推奨)**: 最高品質の日本語音声合成
- **pyttsx3**: オフライン環境での音声合成
- **espeak**: バックアップ音声エンジン

## 📋 システム要件

- **Python**: 3.7以上
- **データベース**: MySQL 5.7以上 または Docker
- **ハードウェア**: AMB P3デコーダー（ネットワーク接続対応）
- **ブラウザ**: モダンWebブラウザ
- **音声出力**: スピーカーまたはヘッドフォン

## 🚀 クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/hama-jp/AMB_RC_Timer.git
cd AMB_RC_Timer
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
uv pip install PyYAML>=6.0
grep -v "PyYAML" requirements.txt | uv pip install -r /dev/stdin

# Web インターフェース用パッケージ
uv pip install flask

# 音声読み上げ用パッケージ
uv pip install gtts pygame
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
    (1, 4000822, 'ドライバーA'),
    (2, 4000823, 'ドライバーB'),
    (3, 4000824, 'ドライバーC'),
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

## 🖥️ Webインターフェース機能

### ライブタイミング表示
- **順位**: ラップ数とベストラップタイムに基づく現在順位
- **カー番号**: データベースで設定されたカー番号
- **ドライバー名**: データベースで設定されたドライバー名
- **ステータス**: レーシング（ラップ完了）またはオントラック（最近のアクティビティ）
- **ラップ数**: 完了した総ラップ数
- **ラストラップタイム**: 最新のラップタイム
- **ベストラップタイム**: 最速ラップタイム（緑色でハイライト）
- **最終アクティビティ**: 最新のトランスポンダーパス時刻

### 最近のパス表示
- トランスポンダー検出のリアルタイムフィード
- トランスポンダーID、信号強度、タイムスタンプを表示
- 最新のアクティビティに自動スクロール

### 🎛️ 音声コントロール
- **音声有効/無効**: 音声読み上げのオン/オフ切り替え
- **音量調整**: 0-100%の音量調整
- **読み上げ速度**: 50-300 WPMの速度調整
- **読み上げスタイル**:
  - **カー番号含む**: オフ（デフォルト）/ オン
  - **ラップ番号含む**: オフ（デフォルト）/ オン
  - **定期全車読み上げ**: オフ（デフォルト）/ オン（30秒間隔）
- **音声テスト**: "音声テスト。RCカータイマーシステムが正常に動作しています。"
- **全車タイム読み上げ**: 手動で全車の現在タイムを読み上げ
- **レースリセット**: レース状態のリセット

### 自動更新
- 2秒間隔での自動更新
- ライブステータスインジケーターで接続状態を表示
- 最大16台のRCカーを同時表示

## 🗄️ データベーススキーマ

システムでは5つの主要テーブルを使用：

- **passes**: AMBデコーダーからの生トランスポンダー読み取りデータ
- **laps**: レースセッション内の検証済みラップタイム
- **heats**: レースセッション管理
- **cars**: トランスポンダーとRCカー/ドライバーのマッピング
- **settings**: ランタイム設定の保存

## 🔧 トラブルシューティング

### AMBデコーダー接続問題

```bash
# デコーダーへの直接接続テスト
python -c "
from AmbP3.decoder import Connection
conn = Connection('192.168.1.21', 5403)  # IPアドレスを調整
conn.connect()
print('接続成功！')
conn.close()
"
```

### MySQL接続問題

```bash
# データベース接続テスト
python -c "
from AmbP3.write import open_mysql_connection
conn = open_mysql_connection(user='kart', db='karts', password='karts', host='127.0.0.1', port=3307)
print('データベース接続成功！')
conn.close()
"
```

### 音声出力問題

```bash
# 音声エンジンのテスト
python -c "
from AmbP3.voice_announcer import VoiceAnnouncer
announcer = VoiceAnnouncer(enabled=True, engine='auto')
print(f'使用中の音声エンジン: {announcer.engine_type}')
announcer.test_voice()
"
```

### システム状態確認

```bash
# 最近のタイミングデータの確認
tail -f /tmp/out.log

# データベースアクティビティの確認
python -c "
from AmbP3.write import open_mysql_connection
conn = open_mysql_connection(user='kart', db='karts', password='karts', host='127.0.0.1', port=3307)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM passes')
print(f'総パス数: {cursor.fetchone()[0]}')
conn.close()
"
```

## 🏗️ システム構成

```
AMB P3デコーダー（ハードウェア）
    ↓ TCP Socket（ポート5403）
amb_client.py（データ収集）
    ↓ プロトコルデコード
MySQL データベース（データ保存）
    ↓ Web API
web_app.py（Flask Webサーバー）
    ↓ HTTP（ポート5000）
Webブラウザ（ライブ表示）
    ↓ 音声出力
Google TTS / pygame（音声読み上げ）
```

## 🧪 開発・テスト

### コード品質チェック

```bash
# リンターの実行
flake8
```

### 音声システムテスト

```bash
# 音声アナウンサーの独立テスト
python -c "
from AmbP3.voice_announcer import VoiceAnnouncer
announcer = VoiceAnnouncer(enabled=True, engine='auto')
print(f'エンジンタイプ: {announcer.engine_type}')
announcer.test_voice()
"

# 個別ラップアナウンステスト
python -c "
from AmbP3.voice_announcer import VoiceAnnouncer
announcer = VoiceAnnouncer(enabled=True)
announcer.announce_lap_time(5, 3, 65.234, is_best=True, simple_mode=True)
"
```

### ファイル構成

```
AMB_RC_Timer/
├── AmbP3/                 # コアタイミングシステムパッケージ
│   ├── config.py         # 設定管理
│   ├── decoder.py        # AMB P3プロトコル処理
│   ├── records.py        # プロトコルメッセージ定義
│   ├── write.py          # データベース操作
│   ├── voice_announcer.py # 音声読み上げシステム
│   └── ...
├── templates/            # Webインターフェーステンプレート
│   └── index.html       # メインダッシュボード
├── amb_client.py        # メインタイミングクライアント
├── web_app.py          # Flask Webアプリケーション
├── conf.yaml           # 設定ファイル
├── schema              # MySQL データベーススキーマ
├── requirements.txt    # Python依存関係
├── setup.sh           # 自動セットアップスクリプト
├── CLAUDE.md          # 開発ガイドライン
├── README.md          # 英語版README
└── README_ja.md       # 日本語版README（このファイル）
```

## 📚 API リファレンス

### メインエンドポイント

- `GET /` - メインダッシュボード
- `GET /api/lap_times` - 現在のラップタイム（JSON）
- `GET /api/recent_passes` - 最近のトランスポンダーパス（JSON）

### 音声制御API

- `GET /api/voice/settings` - 音声設定の取得
- `POST /api/voice/settings` - 音声設定の更新
- `POST /api/voice/test` - 音声テスト
- `POST /api/voice/announce` - 手動音声アナウンス
- `POST /api/voice/announce_all` - 全車タイム読み上げ
- `GET/POST /api/voice/announcement_settings` - 読み上げスタイル設定

### レース管理API

- `POST /api/race/reset` - レース状態のリセット

## 🎯 使用例

### 基本的な使用フロー

1. **AMBデコーダーの設置とネットワーク設定**
2. **システムのセットアップと起動**
3. **Webブラウザでダッシュボードにアクセス**
4. **音声設定の調整（必要に応じて）**
5. **レース開始とリアルタイム監視**

### 音声設定の使い分け

- **練習走行**: シンプルモード（時間のみ）
- **予選・決勝**: 詳細モード（ラップ数・カー番号含む）
- **エンデューロレース**: 定期全車読み上げ有効

## 🤝 コントリビューション

1. リポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを開く

## 📄 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。

## 🔗 関連プロジェクト

- [AMB Web](https://github.com/vmindru/ambweb) - 代替Webインターフェース
- [AMB Docker](https://github.com/br0ziliy/amb-docker) - Docker展開

## 📞 サポート

問題や質問については：

1. 上記のトラブルシューティングセクションを確認
2. `/tmp/out.log` と `/tmp/amb_raw.log` のログを確認
3. 詳細なエラー情報と共にGitHubでIssueを開く

## 📈 今後の開発予定

- [ ] エクスポート機能（CSV、PDF）
- [ ] 複数レースセッション管理
- [ ] カスタム音声メッセージ
- [ ] モバイルアプリ版
- [ ] クラウド同期機能

## 🙏 謝辞

このプロジェクトは以下の技術・ライブラリを使用しています：

- **AMB (Amsterdam Micro Broadcasting)** - P3タイミングデコーダー
- **Google Text-to-Speech** - 高品質日本語音声合成
- **Flask** - Webアプリケーションフレームワーク
- **MySQL** - データベース管理システム
- **pygame** - 音声再生ライブラリ

---

**Happy RC Racing! 🏎️🎌**

*日本のRCカーレースのために作られた、日本語音声読み上げ機能付きプロフェッショナルタイミングシステム*

## スクリーンショット

### メインダッシュボード
![メインダッシュボード](docs/images/dashboard.png)

### 音声コントロールパネル
![音声コントロール](docs/images/voice-control.png)

### ライブタイミング
![ライブタイミング](docs/images/live-timing.png)