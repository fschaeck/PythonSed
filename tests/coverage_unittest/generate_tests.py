#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import re
import sys


PY2 = sys.version_info[0] == 2
OPEN_ARGS = {} if PY2 else {'encoding': 'latin-1'}


def getsection(lines, i, delim):
    i += 1
    i0 = i
    while i < len(lines) and not lines[i].startswith(delim):
        i += 1
    if i == len(lines):
        print('Test not complete')
        return None, i
    else:
        return lines[i0:i], i


def generate_from_testsuite_file(testsuite):
    # testsuite is a suite file

    test_dir = os.path.abspath(os.path.dirname(__file__))

    test_class_name = re.sub('[^a-zA-Z0-9]', '_', os.path.basename(testsuite))
    test_class_name = re.sub('_+', '_', test_class_name)
    test_class_name = re.sub('_+$', '', test_class_name)
    test_class_dir = os.path.join(test_dir, test_class_name)
    if not os.path.exists(test_class_dir):
        os.mkdir(test_class_dir)
    test_class_file_name = os.path.join(test_class_dir,
                                        'generated_test_'+test_class_name+'.py')
    print('Generating test cases in '+test_class_file_name)
    with open(os.path.join(test_dir, test_class_file_name),
              'wt', **OPEN_ARGS) as class_file:
        class_file.write("""\
from tests.coverage_unittest.sed_unittest import PythonSedTestCase


class sed_unittest_{classname}(PythonSedTestCase):
""".format(classname=test_class_name))
        with open(testsuite, 'rt', **OPEN_ARGS) as f:
            lines = [line.rstrip('\r\n') for line in f.readlines()]

        last_script = None
        last_data = None
        last_result = None

        idx = 0
        i = 0
        while i < len(lines):
            # find first delimiter
            while i < len(lines) and not re.match(r'(\S)\1\1', lines[i]):
                i += 1
            if i == len(lines):
                break
            delim = lines[i][0:3]

            title, i = getsection(lines, i, delim)
            script, i = getsection(lines, i, delim)
            data, i = getsection(lines, i, delim)
            result, i = getsection(lines, i, delim)

            idx += 1
            i += 1

            title = ' '.join(title)
            name = re.sub('[^a-zA-Z0-9]', '_', title)
            name = re.sub('_+', '_', name)
            name = re.sub('_+$', '', name)

            if script == '':
                if last_script is None:
                    print('error: empty script on first test')
                    sys.exit(1)
                else:
                    script = last_script
            last_script = script

            if len(data) == 0:
                if last_data is None:
                    print('error: empty data on first test')
                    sys.exit(1)
                else:
                    data = last_data
            last_data = data

            if len(result) == 0:
                if last_result is None:
                    print('error: empty result on first test')
                    sys.exit(1)
                else:
                    result = last_result
            last_result = result

            if result == ['???']:
                exit_code = 1
                result = None
            else:
                exit_code = 0

            class_file.write(
r"""
    def test_{idx:03d}_{name}(self):
        self.run_test_against_object(  # noqa: E122
            debug=0,              # debug level (0..3)
            scripts=[[
r'''{script}
''']],                                # literal script strings (as list)
            inputs=[[
r'''{data}
''']],                                # literal input strings (as list)
            stdout=(
r'''{result}
'''),                                  # expected output to stdout
            exit_code={code},          # expected exit code
            )
""".format(idx=idx, name=name, script='\n'.join(script), data='\n'.join(data), result=('\n'.join(result) if result is not None else ''), code=exit_code))  # noqa: E501
    return


if __name__ == '__main__':
    for file_name in sys.argv[1:]:
        generate_from_testsuite_file(file_name)
