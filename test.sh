#!/bin/bash

cd "$( dirname "$0" )"
set -v
export LULZ_CONF=$PWD/lulz.cfg
exec py.test --ignore=build --pep8 -v --cov=LulzHistory --cov-report=term-missing LulzHistory
