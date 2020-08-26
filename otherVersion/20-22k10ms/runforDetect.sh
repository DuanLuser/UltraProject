#!/bin/bash

python3 record.py $1 $2 &
python3 play.py $3 &