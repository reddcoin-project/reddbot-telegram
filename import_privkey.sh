#!/bin/bash

# Import private key

read -sp 'Please enter private keys separated by space: ' privkey_list
echo ''

for privkey in $privkey_list
do
  echo 'Importing key: $privkey'
  reddcoin-cli importprivkey $privkey "" false
done

echo ''
echo 'Blockchain data will now be rescanned...'
echo 'Stopping Reddcoin Core...'
reddcoin-cli stop
echo 'Waiting a few seconds...'
sleep 10
echo 'Starting Reddcoin Core again - Don't forget to unlock your wallet when blockchain rescan is done...'
reddcoind -rescan