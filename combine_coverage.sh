#!/usr/bin/env bash

root_path=$(dirname $(realpath $0))
coverage combine
coverage xml -o $root_path/reports/coverage.xml -i
