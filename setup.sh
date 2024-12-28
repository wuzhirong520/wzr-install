#!/bin/bash

set -e

ROOT_PATH=$(dirname "$(realpath "$0")")
# echo "$ROOT_PATH"

START_STRING="########## WZR install Tools #############"
END_STRING="#########################################"

INIT_INFO="export PATH=\$PATH:$ROOT_PATH/bin:$ROOT_PATH/usr/bin:$ROOT_PATH/usr/local/bin"
INIT_INFO="$INIT_INFO\nexport LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:$ROOT_PATH/usr/lib:$ROOT_PATH/usr/local/lib:$ROOT_PATH/usr/lib/x86_64-linux-gnu"
INIT_INFO="$INIT_INFO\nexport C_INCLUDE_PATH=\$C_INCLUDE_PATH:$ROOT_PATH/usr/include"
INIT_INFO="$INIT_INFO\nexport CPLUS_INCLUDE_PATH=\$CPLUS_INCLUDE_PATH:$ROOT_PATH/usr/include"
INIT_INFO="$INIT_INFO\nexport MANPATH=\$MANPATH:$ROOT_PATH/usr/share/man"

# echo -e "$INIT_INFO"

if ! grep -q "$START_STRING" "$HOME/.bashrc"; then
    echo "Not initialized yet, initializing Now ..."
    echo "" >> "$HOME/.bashrc"
    echo "$START_STRING" >> "$HOME/.bashrc"
    echo -e "$INIT_INFO" >> "$HOME/.bashrc"
    echo "$END_STRING" >> "$HOME/.bashrc"
else
    echo "Error ! Already initialized, please delele it first."
fi

