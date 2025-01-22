#!/bin/bash

# Unlock your wallet

read -sp 'Please enter your wallet passphrase to unlock the wallet: ' passphrase
echo ''

timeout=999999999 #32 years
anonymizeonly=false #true is for staking only

reddcoin-cli walletpassphrase $passphrase $timeout $anonymizeonly
