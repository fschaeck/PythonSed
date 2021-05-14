#!/usr/bin/env python

from __future__ import print_function


import argparse
import os
import re
import subprocess
import sys
import time

from PythonSed import Sed, SedException


BRIEF = """\
test-suite.py - unit testing utility for sed - sed.godrago.net\
"""

VERSION = '1.00'

LICENSE = """\
Copyright (c) 2014 Gilles Arcas-Luque (gilles dot arcas at gmail dot com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


if sys.version_info[0] == 2:
    OPEN_ARGS = {}
else:
    from io import open as open
    OPEN_ARGS = {'encoding': 'latin-1'}

# -- Base class for tests ----------------------------------------------------


class BaseTest:
    def __init__(self, title):
        self.title = title
        self.script = None
        self.input = None
        self.result = None
        self.wgood = None
        self.scriptname = None
        self.inputname = None
        self.goodname = None
        self.res_output = None
        self.run_output = []
        self.no_autoprint = None
        self.regexp_extended = None
        self.current_dir = None
        self.error_expected = False

    def run(self, binary=None, debug=False):

        if binary is None:
            self.run_output = run_python_sed(self.scriptname, self.inputname,
                                             self.no_autoprint,
                                             self.regexp_extended, debug)
        else:
            self.run_output = run_binary_sed(self.scriptname, self.inputname,
                                             self.no_autoprint,
                                             self.regexp_extended, debug,
                                             binary)

    def checktest(self, ntest, wgood):
        # common check routine
        # derived class must change directory if necessary

        if self.error_expected:
            ref_output = []
        else:
            try:
                with open(self.goodname, 'rt', **OPEN_ARGS) as f:
                    ref_output = f.readlines()
            except IOError:
                print('error reading %s' % self.goodname)
                sys.exit(1)

        if self.run_output is None:
            run_output = []
        else:
            run_output = self.run_output

        return checktest(ntest, self.title, ref_output, run_output, wgood)

    def ignore(self, testnum):
        print('Test %3d ignored: %s' % (testnum, self.title))

    def postproc(self):
        pass


# -- Collection of tests in suite file ---------------------------------------


class SuiteTest(BaseTest):
    # test found in suite file

    def __init__(self, testsuite, title, script, inputlines, resultlines):
        BaseTest.__init__(self, testsuite+': '+title[0])

        self.scriptname = 'test-tmp-script.sed'
        self.inputname = 'test-tmp-script.inp'
        self.goodname = 'test-tmp-script.good'
        self.flagsname = None

        # script, input and result may be empty. In that case, the
        # previously defined entity is used.
        self.script = '' if script == [] else script
        self.input = '' if inputlines == [] else inputlines
        self.result = '' if resultlines == [] else resultlines
        self.error_expected = self.result is None

    def prepare(self):

        # write script
        with open(self.scriptname, 'wt', **OPEN_ARGS) as f:
            for line in self.script:
                print(line, file=f)

        # write input file
        with open(self.inputname, 'wt', **OPEN_ARGS) as f:
            for line in self.input:
                print(line, file=f)

        # write expected result
        if self.error_expected:
            pass
        else:
            with open(self.goodname, 'wt', **OPEN_ARGS) as f:
                for line in self.result:
                    print(line, file=f)

        # set autoprint flag (set later on when reading first line of script)
        self.no_autoprint = None

        # handle #r extended flag
        # n must appear first to stay compatible with standard
        self.regexp_extended = False
        line1 = self.script[0]
        if line1.startswith('#r') or line1.startswith('#nr'):
            self.regexp_extended = True

        return True

    def check(self, ntest):

        return BaseTest.checktest(self, ntest, [])


# -- Collection of tests in directory ----------------------------------------


class FolderTest(BaseTest):
    # test found in folder

    def __init__(self, scriptname, folder):
        BaseTest.__init__(self, os.path.join(folder, scriptname))

        self.scriptname = scriptname
        self.inputname = scriptname.replace('.sed', '.inp')
        self.goodname = scriptname.replace('.sed', '.good')
        self.flagsname = scriptname.replace('.sed', '.flags')

        self.folder = folder
        self.error_expected = False

    def prepare(self):
        self.current_dir = os.getcwd()
        os.chdir(self.folder)

        if not os.path.isfile(self.inputname):
            print('%s: input file not found' % self.inputname)
            os.chdir(self.current_dir)
            return False

        if not os.path.isfile(self.goodname):
            # expected result file is missing when waiting for exception
            self.error_expected = True

        # read flags file if any
        self.no_autoprint = False
        self.regexp_extended = False
        if os.path.isfile(self.flagsname):
            with open(self.flagsname, 'rt', **OPEN_ARGS) as f:
                for line in f:
                    self.no_autoprint = self.no_autoprint or ('-n' in line)
                    self.regexp_extended = self.regexp_extended or ('-r' in line)

        # find list of wgood files (files written by w command or w switch)
        wgood = os.listdir('.')
        self.wgood = [x for x in wgood if self.scriptname.replace('.sed', '.wgood') in x]

        # delete wout files if any
        for fgood in self.wgood:
            wout = fgood.replace('.wgood', '.wout')
            if os.path.isfile(wout):
                os.remove(wout)

        return True

    def check(self, ntest):

        res = BaseTest.checktest(self, ntest, self.wgood)
        return res

    def postproc(self):
        os.chdir(self.current_dir)


# -- Helpers -----------------------------------------------------------------


def run_python_sed(scriptname, inputfile, no_autoprint, regexp_extended, debug):
    sed = Sed()
    sed.no_autoprint = no_autoprint
    sed.regexp_extended = regexp_extended
    sed.encoding = 'latin-1'
    if debug:
        sed.debug = 2

    try:
        # all loading methods must give the same result
        mode = 1  # 1, 2, 3

        if mode == 1:
            sed.load_script(scriptname)
        elif mode == 2:
            with open(scriptname, 'rt', **OPEN_ARGS) as f:
                string = ''.join(f.readlines())
            sed.load_string(string)
        elif mode == 3:
            with open(scriptname, 'rt', **OPEN_ARGS) as f:
                string_list = f.readlines()
            sed.load_string_list(string_list)
        else:
            raise Exception()

        return sed.apply(inputfile, None)
    except SedException as e:
        print(e.message, file=sys.stderr)
        return None


def run_binary_sed(scriptname, inputfile, no_autoprint, regexp_extended,
                   binary, debug):
    template = r'%s %s %s %s -f %s %s'
    command_line = template % (binary,
                               '-n' if no_autoprint else '',
                               '-r' if regexp_extended else '',
                               '-d' if debug else '',
                               scriptname,
                               inputfile)
    try:
        output = check_output(command_line, shell=True)

        # ascii utf-8 iso8859_15 latin_1
        if sys.version_info[0] == 2:
            pass
        else:
            output = output.decode('latin-1', errors='replace')

        output = output.split('\n')
        return output
    except subprocess.CalledProcessError as e:
        print(e)
        return None


def checktest(testnum, testname, ref_output, run_output, wgood):
    # compare expected and obtained results

    # outputs may be None if exception, will be compared as list
    if run_output is None:
        run_output = []
    if ref_output is None:
        ref_output = []

    # compare outputs
    result, diff = list_compare('ref', 'out', ref_output, run_output)

    # compare files written by w command or w switch
    for fgood in wgood:
        wout = fgood.replace('.wgood', '.wout')
        result2, diff2 = file_compare(fgood, wout)
        result = result and result2
        diff.extend(diff2)

    # feedback
    if result:
        print('Test %3d success: %s' % (testnum, testname))
    else:
        print('Test %3d failure: %s' % (testnum, testname))
        for x in diff:
            print(str(x))

    return result


def list_compare(tag1, tag2, list1, list2):

    MISSING_MARKER = '<missing>'
    UNEXPECTED_MARKER = '<unexpected>'

    max_lst_len = max(len(list1), len(list2))
    if max_lst_len == 0:
        return True, []

    # make sure both lists have same length
    list1.extend([None] * (max_lst_len - len(list1)))
    list2.extend([None] * (max_lst_len - len(list2)))

    max_txt_len_1 = max(list((len(UNEXPECTED_MARKER) if txt is None else len(txt))
                             for txt in list1)+[len(tag1)])
    max_txt_len_2 = max(list((len(MISSING_MARKER) if txt is None else len(txt))
                             for txt in list2)+[len(tag2)])

    diff = ['']
    res = True
    diff.append('|  No | ? | {tag1:<{txtlen1}.{txtlen1}s} | {tag2:<{txtlen2}.{txtlen2}s} |'
                .format(tag1=tag1, tag2=tag2, txtlen1=max_txt_len_1, txtlen2=max_txt_len_2))
    for i, (x, y) in enumerate(zip(list1, list2)):
        if x != y and x is not None and y is not None:
            if x.rstrip('\r\n') == y.rstrip('\r\n'):
                x = x.replace('\r', '\\r')
                x = x.replace('\n', '\\n')
                y = y.replace('\r', '\\r')
                y = y.replace('\n', '\\n')
        diff.append(('| {idx:>3d} | {equal:1.1s} | {line1:<{txtlen1}.{txtlen1}s} ' +
                     '| {line2:<{txtlen2}.{txtlen2}s} |')
                    .format(idx=i+1,
                            equal=(' ' if x == y else '*'),
                            txtlen1=max_txt_len_1,
                            txtlen2=max_txt_len_2,
                            line1=UNEXPECTED_MARKER if x is None else x.rstrip('\r\n'),
                            line2=MISSING_MARKER if y is None else y.rstrip('\r\n')))
        res = res and x == y
    return res, diff


def file_compare(fn1, fn2):
    with open(fn1, 'rt', **OPEN_ARGS) as f:
        lines1 = f.readlines()
    with open(fn2, 'rt', **OPEN_ARGS) as f:
        lines2 = f.readlines()
    return list_compare(fn1, fn2, lines1, lines2)


def check_output(*popenargs, **kwargs):
    # maintain compatibility with 2.6
    # https://gist.github.com/edufelipe/1027906
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
            error = subprocess.CalledProcessError(retcode, cmd)
            error.output = output
            raise error
    return output


# -- Loading test suites -----------------------------------------------------


def load_testsuite(testsuite):
    # dispatch on test suite type

    if testsuite[0] == '@':
        if os.path.isfile(testsuite[1:]):
            all_tests = load_testsuite_batch(testsuite[1:])
        else:
            all_tests = list()
            print('Test suite not found:', testsuite)
    elif testsuite.endswith('.suite') and os.path.isfile(testsuite):
        all_tests = load_testsuite_file(testsuite)
    elif os.path.isdir(testsuite):
        all_tests = load_testsuite_folder(testsuite)
    else:
        all_tests = list()
        print('Test suite not found:', testsuite)

    return all_tests


def load_testsuite_file(testsuite):
    # testsuite is a suite file

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

    tests = list()

    with open(testsuite, 'rt', **OPEN_ARGS) as f:
        lines = [line.rstrip('\r\n') for line in f.readlines()]

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
        inputlines, i = getsection(lines, i, delim)
        resultlines, i = getsection(lines, i, delim)
        if resultlines == ['???']:
            resultlines = None

        i += 1

        tests.append(SuiteTest(testsuite, title, script, inputlines, resultlines))
        test = tests[-1]
        index = len(tests) - 1

        if test.script == '':
            if index == 0:
                print('test-suite error: empty script on first test')
                sys.exit(1)
            else:
                test.script = tests[index-1].script

        if test.input == '':
            if index == 0:
                print('test-suite error: empty input on first test')
                sys.exit(1)
            else:
                test.input = tests[index-1].input

        if test.result == '':
            if index == 0:
                print('test-suite error: empty result on first test')
                sys.exit(1)
            else:
                test.result = tests[index-1].result

    return tests


def load_testsuite_folder(testsuite):
    # testsuite is a directory path

    current_dir = os.getcwd()
    os.chdir(testsuite)

    scripts = sorted([x for x in os.listdir('.') if x.endswith('.sed')])
    tests = list()
    for script in scripts:
        tests.append(FolderTest(script, testsuite))

    os.chdir(current_dir)

    return tests


def load_testsuite_batch(testsuite):
    # testsuite is a text file containing suite file names or folder names

    all_tests = list()
    with open(testsuite, 'rt', **OPEN_ARGS) as f:
        for suite in [line.strip() for line in f]:
            all_tests.extend(load_testsuite(suite))
    return all_tests


# -- Running tests suite -----------------------------------------------------


def run_testsuite(tests, target, binary, exclude, elapsed_only, debug):
    start = time.time()
    result = True
    debug = debug or target is not None
    n_succeeded = 0
    n_failed = 0
    n_ignored = 0
    for index, test in enumerate(tests):

        # numbers are printed starting from 1
        user_index = index + 1

        if test_requested(user_index, target):
            if test_ignored(test, exclude):
                test.ignore(user_index)
                n_ignored += 1
            else:
                if test.prepare():
                    test.run(binary, debug=debug)
                    if elapsed_only:
                        pass
                    else:
                        res = test.check(user_index)
                        if not res:
                            n_failed += 1
                        else:
                            n_succeeded += 1
                        result = result and res
                    test.postproc()
                else:
                    test.ignore(user_index)
                    n_ignored += 1

    end = time.time()
    elapsed = end - start

    if result:
        print('All tests ok (succeeded: %d, ignored: %d)' % (n_succeeded, n_ignored))
        print('Elapsed: %.3fs' % elapsed)
        sys.exit(0)
    else:
        print('Test failure (succeeded: %d, ignored: %d, failed: %d)'
              % (n_succeeded, n_ignored, n_failed))
        print('Elapsed: %.3fs' % elapsed)
        sys.exit(1)


def test_requested(index, target):
    if target is None:
        return True
    else:
        return index == target


def test_ignored(test, exclude):
    if test.title in exclude:
        return True
    else:
        return False


# -- Main --------------------------------------------------------------------


def parse_command_line():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
<file> may be:
    - a text file implementing tests, cf. unit.suite
    - a folder containing scripts and data, cf. testsuite\\
    - a batch reference, if prefixed with @, containing file names or
      folder names cf. all_tests.suites
""")
    parser.add_argument("-b", "--binary",
                        help="binary sed to run instead of pythonsed",
                        action="store",
                        dest="binary",
                        metavar='<sed command>')
    parser.add_argument("-x", "--exclude",
                        help="name of file with list of tests to exclude",
                        action="store",
                        dest="exclude",
                        metavar='<exclude file>')
    parser.add_argument("-e", "--elapsed-only",
                        help='display elapsed time only',
                        action="store_true",
                        dest="elapsed_only")
    parser.add_argument("-d", "--debug",
                        help='switch on debugging output',
                        action="store_true")
    parser.add_argument("file",
                        metavar="<file>",
                        help='test specifications to load')
    parser.add_argument("target",
                        type=int,
                        metavar='<test number>',
                        nargs='?',
                        help='specfic test to run')

    return parser, parser.parse_args()


def main():
    _, args = parse_command_line()

    testsuite = args.file
    if args.target is not None:
        target = int(args.target)
    else:
        target = None

    try:
        # navigate to script directory
        current_dir = os.getcwd()
        test_dir = os.path.dirname(__file__)
        os.chdir(test_dir)

        if args.exclude:
            try:
                with open(args.exclude, 'rt', **OPEN_ARGS) as f:
                    exclude = [line.strip() for line in f.readlines()]
            except IOError:
                print('Error reading exclude file:', args.exclude)
                sys.exit(1)
        else:
            exclude = list()

        all_tests = load_testsuite(testsuite)
        run_testsuite(all_tests, target, args.binary, exclude, args.elapsed_only, args.debug)

    finally:
        os.chdir(current_dir)


if __name__ == "__main__":
    main()
