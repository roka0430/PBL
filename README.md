# PBL6 自動水やり機

## セットアップ

### プロキシの設定

```bash
sudo nano /etc/apt/apt.conf
```
または
```bash
sudo nano /etc/apt/apt.conf.d/80proxy
```

```
Acquire::http::Proxy "http://example.com:PORT/";
Acquire::https::Proxy "http://example.com:PORT/";
```

### パッケージ情報の更新

```bash
sudo apt update
```

### パッケージのアップグレード

```bash
sudo apt upgrade -y
```

### 必要なパッケージのインストール

```bash
sudo apt install -y git python3 python3-pip python3-venv
```

### インストールの確認

```bash
git --version
python3 --version
pip3 --version
```

### リポジトリの取得

```bash
git clone https://github.com/roka0430/PBL.git
```

```bash
cd PBL
ls
```

### Python仮想環境の作成・有効化

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Pythonライブラリのインストール

```bash
pip install -r requirements.txt
```

### `.env`の生成

```bash
python3 tools/setup_env.py
```

## ターミナルからの実行

### Python仮想環境を有効化

```bash
source .venv/bin/activate
```

### 実行

```bash
python3 app.py
```

## 自動起動の設定

### systemdサービスの作成

```bash
sudo nano /etc/systemd/system/pbl.service
```

```ini
[Unit]
Description=PBL Automatic Watering System
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<USER_NAME>
WorkingDirectory=/home/<USER_NAME>/PBL
ExecStart=/home/<USER_NAME>/PBL/.venv/bin/python3 /home/<USER_NAME>/PBL/app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### systemdの再読み込み

```bash
sudo systemctl daemon-reload
```

### アプリケーションの起動確認

```bash
sudo systemctl start pbl.service
sudo systemctl status pbl.service
```

以下のように表示されればよい。

```bash
Active: active (running)
```

### ログの確認

```bash
sudo journalctl -u pbl.service
```

リアルタイムでログを確認する場合：

```bash
sudo journalctl -u pbl.service -f
```

### 自動起動の有効化

```bash
sudo systemctl enable pbl.service
```

有効化の確認：

```bash
systemctl is-enabled pbl.service
```

無効化：

```bash
sudo systemctl disable pbl.service
```

### アプリケーションの再起動

```bash
sudo systemctl restart pbl.service
```
