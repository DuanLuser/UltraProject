#!/bin/bash

python3 record.py $1 $2 $3 &
python3 play.py $4 &