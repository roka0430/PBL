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
