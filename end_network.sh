#!/bin/sh

safe auth stop
rm $HOME/.safe/authd/logs/sn_authd.log
safe node killall
rm -r $HOME/.safe/node/baby-fleming-nodes/
