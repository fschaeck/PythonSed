#!/bin/bash

export PYENV_VIRTUALENV_DISABLE_PROMPT=1
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
export PYTHONPATH=./src

coverage erase
if [[ -z "$1" || "$1" == "2" ]]
then
  echo "Activating Python 2"
  pyenv activate sed.py.2
  pytest --cov=PythonSed --cov-report=xml:./coverage-py2.xml tests/coverage_unittest
fi

if [[ -z "$1" || "$1" == "3" ]]
then
  echo "Activating Python 3"
  pyenv activate sed.py.3
  if [[ -z "$1" ]]
  then
    pytest --cov-append --cov=PythonSed --cov-report=xml:./coverage-py3.xml tests/coverage_unittest
  else
    pytest --cov=PythonSed --cov-report=xml:./coverage-py3.xml tests/coverage_unittest
  fi
fi

coverage html
coverage report
