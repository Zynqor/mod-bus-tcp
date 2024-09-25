#!/bin/bash
BASE_DIR=$(cd $(dirname $0); pwd)
cd $BASE_DIR
nohup python Web.py >/dev/null 2>&1 &