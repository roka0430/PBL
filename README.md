# 自動水やり機「MizuMori」

## Raspberry Pi

### SSH接続

```bash
ssh pi@<IP Address>
```


## 実行環境

### プロキシの適用

```bash
export http_proxy="http://proxy.example.com:PORT"
export https_proxy="http://proxy.example.com:PORT"
```

### パッケージのupdate/upgrade

```bash
sudo apt update
sudo apt upgrade -y
```

### リポジトリのclone

```bash
git clone https://github.com/roka0430/PBL.git
```

### リポジトリの強制上書き

```bash
git fetch origin
git reset --hard origin/main
```

### Python仮想環境の有効化

```bash
source .venv/bin/activate
```

### Pythonライブラリのインストール

```bash
pip install -r requirements.txt
```

### DHT20用ライブラリのインストール

```bash
pip install adafruit-circuitpython-ahtx0
```

以下が使えるようになる

```python
import board
import adafruit_ahtx0
```

### .envの生成

```bash
python3 tools/setup_env.py
```

## SPI/I2C有効化

### SPI

```bash
sudo raspi-config
```

```
1. Interface Optionsを選択
2. SPIを選択
3. Enableを選択
```

```bash
sudo reboot
```

### I2C

```bash
sudo raspi-config
```

```
1. Interface Optionsを選択
2. I2Cを選択
3. Enableを選択
```

```bash
sudo reboot
```

## 自動起動

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

## リバースプロキシ

### Caddyのインストール

```bash
sudo apt install --y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### Caddyのインストールの確認

```bash
caddy version
```

### Caddyのsystemdの確認

サービスの状態：

```bash
sudo systemctl status caddy
```

自動起動が有効か：

```bash
sudo systemctl is-enabled caddy
```

自動起動を有効化する：

```bash
sudo systemctl enable caddy
```

### Caddyfileの設定

```bash
sudo nano /etc/caddy/Caddyfile
```

```bash
:80 {
    reverse_proxy 127.0.0.1:5000
}
```

### Caddyfileの検証

フォーマットの整形：

```bash
sudo caddy fmt --overwrite /etc/caddy/Caddyfile
```

構文の検証：

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
```

### Caddyの再起動と設定の反映

```bash
sudo systemctl reload caddy
```

状態の確認：

```bash
sudo systemctl status caddy
```
