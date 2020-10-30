#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"; cd ..; cd .. >/dev/null 2>&1 && pwd )"

export PYTHONPATH=$DIR/iap:$DIR/webiap:$DIR/mconvert:$DIR/pyfig