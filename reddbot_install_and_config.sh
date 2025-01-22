#!/bin/bash

# Check if files for installation are in current directory
if [[ ! -f config.py ]] ;
  then
    echo "Could not find config.py in current directory!"
    exit
fi
if [[ ! -f requirements.txt ]] ;
  then
    echo "Could not find requirements.txt in current directory!"
    exit
fi
if [[ ! -f reddbot.sql ]] ;
  then
    echo "Could not find reddbot.sql in current directory!"
    exit
fi

# Asking user for inputs for replacing values in config file
read -p 'Telegram bot name (starting with @ symbol): ' TELEGRAM_BOT_NAME
read -p 'Telegram bot token (<8-10 digits:35 chars>): ' TELEGRAM_BOT_TOKEN
sed -i "s/bot_name = None/bot_name = \"$TELEGRAM_BOT_NAME\"/g" config.py
sed -i "s/bot_token = None/bot_token = \"$TELEGRAM_BOT_TOKEN\"/g" config.py

# Install dependencies
sudo apt update && sudo apt -y install redis-server python3 python3-pip python3-venv git unzip curl wget tzdata

# Reconfigure the timezone
sudo ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime
sudo dpkg-reconfigure -f noninteractive tzdata

# Install and configure MySQL server
read MYSQL_DB_PWD < <(date +%s | sha256sum | base64 | head -c 32 ; echo)
wget https://repo.mysql.com//mysql-apt-config_0.8.32-1_all.deb -O mysql.deb
sudo DEBIAN_FRONTEND=noninteractive dpkg -i mysql.deb
rm mysql.deb
sudo apt update
sudo DEBIAN_FRONTEND=noninteractive apt install -y mysql-server
sudo mysql -u root -e "ALTER USER root@localhost IDENTIFIED WITH caching_sha2_password BY '$MYSQL_DB_PWD';"

# Configure redis server
sudo sed -i "s/supervised no/supervised systemd/g" /etc/redis/redis.conf
sudo systemctl restart redis.service

# Configure and install dependencies for Reddcoin Telegram Bot (Reddbot)
sed -i "s/db_mysql_password = None/db_mysql_password = \"$MYSQL_DB_PWD\"/g" config.py
python3 -m venv python_env --system-site-packages
python_env/bin/python3 -m pip install -r requirements.txt
sudo mysql -u root -p$MYSQL_DB_PWD -h localhost < reddbot.sql
chmod +x encrypt_wallet.sh && chmod +x import_privkey.sh && chmod +x unlock_wallet.sh

# Download and configure Reddcoin Core Wallet
arch=$(uname -i)
if [ $arch == 'x86_64' ]; then
    curl https://download.reddcoin.com/bin/reddcoin-core-4.22.8/x86_64-linux-gnu/reddcoin-1d0e612e3f0c-x86_64-linux-gnu.tar.gz -o reddcoin.tar.gz && tar -xf reddcoin.tar.gz && rm reddcoin.tar.gz
fi
if [ $arch == 'aarch64' ]; then
    curl https://download.reddcoin.com/bin/reddcoin-core-4.22.8/aarch64-linux-gnu/reddcoin-1d0e612e3f0c-aarch64-linux-gnu.tar.gz -o reddcoin.tar.gz && tar -xf reddcoin.tar.gz && rm reddcoin.tar.gz
fi
chmod +x reddcoin-1d0e612e3f0c/bin/reddcoin* && sudo mv reddcoin-1d0e612e3f0c/bin/reddcoin* /usr/local/bin
rm -r reddcoin-1d0e612e3f0c
mkdir -p ~/.reddcoin && cd ~/.reddcoin
echo "rpcuser="$USER >> reddcoin.conf
read RPC_PWD < <(date +%s | sha256sum | base64 | head -c 32 ; echo)
echo "rpcpassword="$RPC_PWD >> reddcoin.conf
echo "daemon=1" >> reddcoin.conf

# Download blockchain data
echo "Trying to download blockhain data..."
wget --user-agent="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36" -O rdd_blockchain_v4.zip 'https://onedrive.live.com/download?resid=2680E781C45BBECC%21756&authkey=!AM-gszLRGwPdWX0'
unzip rdd_blockchain_v4.zip && rm rdd_blockchain_v4.zip

# Starting Reddcoin Core Wallet
reddcoind
echo "Waiting 120 seconds until Reddcoin Core Wallet is ready to be encrypted..."
sleep 120
cd ~/reddbot-telegram
read WALLET_PASSPHRASE < <(date +%s | sha256sum | base64 | head -c 32 ; echo)
reddcoin-cli createwallet "reddbot"
reddcoin-cli encryptwallet $WALLET_PASSPHRASE
reddcoin-cli walletpassphrase $WALLET_PASSPHRASE 999999999 false
reddcoin-cli setstaking true true
reddcoin-cli loadwallet "reddbot" true
echo "Reddcoin Core Wallet passphrase is: $WALLET_PASSPHRASE"
echo "Passphrase can be used to unlock wallet using script file unlock_wallet.sh if wallet needs to be restarted."
echo "BE AWARE: This passphrase was not stored somewhere! You need to store it in a safe place for yourself!"