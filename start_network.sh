#!/bin/sh

echo "{\"passphrase\":\"testuserpassphrase\",\"password\":\"testuserpassword\"}" > /tmp/testuser_creds.json

# start new network
safe node run-baby-fleming

# create new account
safe auth start
safe auth create --test-coins --config /tmp/testuser_creds.json
safe auth unlock --self-auth --config /tmp/testuser_creds.json
