#!/bin/bash

# Encrypt your wallet

read -sp 'Please enter a new wallet passphrase: ' passphrase
echo ''

reddcoin-cli encryptwallet $passphrase
