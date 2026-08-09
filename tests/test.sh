#!/bin/bash

# Runs the hidden tests and writes the reward.
# It will be copied to /tests/test.sh and run from the working directory.
#
# NOTE: task.toml sets network_mode = "no-network", so this script cannot
# download anything at verify time. pytest and pytest-json-ctrf must already
# be installed in the image by environment/Dockerfile.

# CTRF produces a standard test report in JSON format which is useful for logging.
pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
