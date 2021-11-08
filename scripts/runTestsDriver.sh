#!/usr/bin/env bash

export CODE_TESTS_PATH="$(pwd)/client/out/test"
export CODE_TESTS_WORKSPACE="$(pwd)/client/testWorkspace"

node "$(pwd)/client/out/test/runTests"
