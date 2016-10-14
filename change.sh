#!/bin/sh
# Автоматическая смена НИМа в TOR
empty -f -i torin -o torout telnet 127.0.0.1 9051
empty -s -o torin "AUTHENTICATE \"password\"\n"
empty -s -o torin "signal NEWNYM\n"
empty -s -o torin "quit\n"
