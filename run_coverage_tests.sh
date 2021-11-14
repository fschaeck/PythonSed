#!/bin/bash

export PYENV_VIRTUALENV_DISABLE_PROMPT=1
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
export PYTHONPATH=/Users/de014490/Development/git/PythonSed

coverage erase
if [[ -z "$1" || "$1" == "2" ]]
then 
  echo "Activating Python 2"
  pyenv activate sed.py.2
  coverage run --source=PythonSed --timid -a -m unittest tests.coverage_unittest.unit_suite.test_unit_suite
fi

if [[ -z "$1" || "$1" == "3" ]]
then 
  echo "Activating Python 3"
  pyenv activate sed.py.3
  coverage run --source=PythonSed --timid -a -m unittest tests.coverage_unittest.unit_suite.test_unit_suite
fi

coverage html
coverage report
