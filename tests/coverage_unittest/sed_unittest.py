# -*- coding: utf-8 -*-
"""Utility for PythonSed unittest testcases"""
from __future__ import print_function, unicode_literals

from io import open as open, StringIO
import codecs
import locale
import logging
import os
import shutil
import sys
import tempfile
import unittest

import PythonSed


DEFAULT_ENCODING = locale.getpreferredencoding()
PY2 = sys.version_info[0] == 2
if PY2:

    def make_unicode(strg, encoding):
        if type(strg) == str:
            return unicode(strg, encoding)
        else:
            return strg

else:

    class unicode(object):  # @ReservedAssignment
        pass

    def make_unicode(strg, encoding):
        if type(strg) == bytes:
            return strg.decode(encoding)
        else:
            return strg

    def unichr(char):  # @ReservedAssignment
        return chr(char)

ON_TRAVIS = 'TRAVIS' in os.environ


class Capture(object):
    def __init__(self, stdin_data):
        if stdin_data is not None:
            if PY2 and type(stdin_data) != unicode or not PY2 and type(stdin_data) != str:
                raise ValueError('Programming error: Capture(stdin_data) not unicode.')
        self._stdin_data = stdin_data  # must be unicode
        self._stdin = None
        self._stdout_data = []
        self._stderr_data = []

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio_out = StringIO()
        self._stderr = sys.stderr
        sys.stderr = self._stringio_err = StringIO()
        if self._stdin_data is not None:
            self._stdin = sys.stdin
            sys.stdin = self._stringio_in = StringIO(self._stdin_data)
        else:
            self._stdin = None
        return self

    def __exit__(self, *args):  # @UnusedVariable
        content = self._stringio_out.getvalue()
        if len(content) == 0:
            pass
        elif content.endswith('\n'):
            self._stdout_data.extend(lne+'\n' for lne in content[:-1].split('\n'))
        else:
            self._stdout_data.extend(lne+'\n' for lne in content.split('\n'))
        sys.stdout = self._stdout
        del self._stringio_out

        content = self._stringio_err.getvalue()
        if len(content) == 0:
            pass
        elif content.endswith('\n'):
            self._stderr_data.extend(lne+'\n' for lne in content[:-1].split('\n'))
        else:
            self._stderr_data.extend(lne+'\n' for lne in content.split('\n'))
        sys.stderr = self._stderr
        del self._stringio_err

        if self._stdin is not None:
            del self._stringio_in
            sys.stdin = self._stdin

    def stdout(self):
        return self._stdout_data

    def stderr(self):
        return self._stderr_data


class PythonSedTestCase(unittest.TestCase):
    """A test case implementing utility methods for testing PythonSed"""

    environment = {}

    def setUp(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.debug('preparing environment...')
        for kn in self.environment:
            if kn not in os.environ:
                v = self.environment[kn]
                self.logger.debug('Setting ${nme} to: {val}'.format(nme=kn, val=v))
                os.environ[kn] = v
        try:
            self.old_cwd = os.getcwd()
        except OSError:
            self.old_cwd = None
        self.test_dir = os.path.abspath(os.path.dirname(sys.modules[self.__module__].__file__))
        self.temp_dir = tempfile.mkdtemp(prefix='sed_unittest.')
        os.chdir(self.temp_dir)

    def tearDown(self):
        if self.old_cwd:
            os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir)

    def create_tempfile(self, encoding, prefix, content):  # expects unicode for content
        (fd, name) = tempfile.mkstemp(dir=self.temp_dir, prefix=prefix)
        with os.fdopen(fd, 'wb') as fle:
            fle.write(codecs.getencoder(encoding)(content)[0])
        return name

    def run_test_against_object(
            self,
            debug=0,              # debug level (0..3)
            encoding=DEFAULT_ENCODING,  # input encoding
            in_place=None,        # edit input files in place
            no_autoprint=False,   # do not print anyhing automatically
            separate=False,       # process input files separately instead of as continous stream
            python_syntax=False,  # use python syntax for regex (-p option)
            extended=False,       # use extended regex syntax (-E option)
            line_length=70,       # default line length for l command
            scripts=[],           # literal script strings (as list) and file names (as string)
            inputs=[],            # literal input strings (as list) and file names (as string)
            output=None,          # write output to this stream/filename (None defaults to stdout)
            stdin=None,           # stdin input to command
            stdout=None,          # expected output to stdout
            stderr=None,          # expected output to stderr
            inplace_content=[],   # expected content of inputs after inplace-editing
            output_files={},      # expected content of files written by the sed script
            exit_code=0,          # expected exit code
            ):

        sed = PythonSed.Sed(debug=debug,
                            encoding=encoding,
                            in_place=in_place,
                            no_autoprint=no_autoprint,
                            separate=separate,
                            sed_compatible=not python_syntax,
                            regexp_extended=extended,
                            line_length=line_length)

        output_stdout = []
        with Capture(stdin) as capture:
            # change to temporary directory, so that the commands
            # r, R, w and W do not need absolute paths for tests
            try:
                for script in scripts:  # @ReservedAssignment
                    if type(script) == list:
                        sed.load_string_list(script)
                    else:
                        sed.load_script(script)
                output_stdout = sed.apply(inputs, output=output)
                actual_exit_code = sed.exit_code
            except PythonSed.SedException as e:
                sys.stderr.write(e.message+'\n')
                actual_exit_code = 1

        if output is None and in_place is None:
            pass
        else:
            output_stdout = capture.stdout()

        self.check_results(
            encoding,
            output_stdout, stdout,
            capture.stderr(), stderr,
            actual_exit_code, exit_code,
            output_files,
            inplace_option=in_place,
            inplace_inputs=inputs,
            inplace_content=inplace_content)

    def run_test_against_main(
            self,
            debug=0,              # debug level (0..3)
            encoding=DEFAULT_ENCODING,   # input encoding
            in_place=None,        # option -i value
            options=[],           # additional options
            scripts=[],           # literal script strings (as list) and file names (as string)
            inputs=[],            # literal input strings (as list) and file names (as string)
            stdin=None,           # stdin input to command
            stdout=None,          # expected output to stdout
            stderr=None,          # expected output to stderr
            output_files={},      # expected content of files written by the sed script
            inplace_content=[],   # results of inplace-editing
            exit_code=0,          # expected exit code
            ):
        args = ['sed.py', '--encoding='+encoding]
        if debug > 0:
            args.append('--debug='+str(debug))

        if in_place is not None:
            args.append('--in-place'+('='+str(in_place) if len(str(in_place)) > 0 else ''))

        args.extend(options)

        for script in scripts:
            if type(script) == list:
                args.append('--expression='+'\n'.join(script))
            else:
                args.append('--file='+script)

        processed_inputs = []
        input_index = 0
        for input in inputs:  # @ReservedAssignment
            input_index += 1
            if type(input) == list:
                processed_inputs.append(
                    self.create_tempfile(encoding, 'literal.{idx}.'.format(idx=input_index),
                                         '\n'.join(make_unicode(lne, encoding) for lne in input)))
            elif type(input) == str or PY2 and type(input) == unicode:
                processed_inputs.append(input)
            else:
                file_name = tempfile.mkstemp(dir=self.temp_dir,
                                             prefix='stream.{idx}.'.format(input_index))
                with open(file_name, 'wt', encoding=encoding) as f:
                    for lne in input.readlines():
                        f.write(lne)
                processed_inputs.append(file_name)

        args.extend(processed_inputs)
        sys.argv = args

        with Capture(stdin) as capture:
            # change to temporary directory, so that the commands
            # r, R, w and W do not need absolute paths for tests
            actual_exit_code = PythonSed.main()

        self.check_results(
            encoding,
            capture.stdout(), stdout,
            capture.stderr(), stderr,
            actual_exit_code, exit_code,
            output_files,
            inplace_option=in_place,
            inplace_inputs=processed_inputs,
            inplace_content=inplace_content)

    def make_list(self, encoding, content):
        if type(content) == str or PY2 and type(content) == unicode:
            if len(content) == 0:
                return []
            content = make_unicode(content, encoding)
            if content.endswith('\n'):
                return list(lne+'\n' for lne in content[:-1].split('\n'))
            else:
                return list(lne+'\n' for lne in content.split('\n'))
        elif type(content) == list:
            return list(make_unicode(lne, encoding) for lne in content)
        raise ValueError('Programming error: invalid content parameter type ({}) for make_list'
                         .format(type(content)))

    def check_output(self, encoding, content_name, expected_content, actual_content):
        MISSING_MARKER = '<missing>'
        UNEXPECTED_MARKER = '<unexpected>'

        list1 = self.make_list(encoding, expected_content)
        list2 = self.make_list(encoding, actual_content)

        content_name = os.path.basename(content_name)
        tag1 = 'expected '+content_name
        tag2 = 'actual '+content_name

        max_lst_len = max(len(list1), len(list2))
        if max_lst_len == 0:
            return []

        # make sure both lists have same length
        list1.extend([None] * (max_lst_len - len(list1)))
        list2.extend([None] * (max_lst_len - len(list2)))

        max_txt_len_1 = max(list(len(UNEXPECTED_MARKER)
                                 if txt is None
                                 else 3*len(txt)-2*len(txt.rstrip('\r\n'))
                                 for txt in list1)+[len(tag1)])
        max_txt_len_2 = max(list(len(MISSING_MARKER)
                                 if txt is None
                                 else 3*len(txt)-2*len(txt.rstrip('\r\n'))
                                 for txt in list2)+[len(tag2)])

        diff = ['']
        equal = True
        diff.append('|  No | ? | {tag1:<{txtlen1}.{txtlen1}s} | {tag2:<{txtlen2}.{txtlen2}s} |'
                    .format(tag1=tag1, tag2=tag2, txtlen1=max_txt_len_1, txtlen2=max_txt_len_2))
        for i, (x, y) in enumerate(zip(list1, list2)):
            if x != y:
                equal = False
                if x is not None and y is not None and x.rstrip('\r\n') == y.rstrip('\r\n'):
                    x = x.replace('\n', '\\n').replace('\r', '\\r')
                    y = y.replace('\n', '\\n').replace('\r', '\\r')
            diff.append('| {idx:>3d} | {equal:1.1s} | {line1:<{txtlen1}.{txtlen1}s} | {line2:<{txtlen2}.{txtlen2}s} |'  # noqa: E501
                        .format(idx=i+1,
                                equal=(' ' if x == y else '*'),
                                txtlen1=max_txt_len_1,
                                txtlen2=max_txt_len_2,
                                line1=UNEXPECTED_MARKER
                                      if x is None
                                      else x.rstrip('\r\n'),  # .replace(' ', '\N{MIDDLE DOT}'),
                                line2=MISSING_MARKER
                                      if y is None
                                      else y.rstrip('\r\n')))  # .replace(' ', '\N{MIDDLE DOT}')))

        return [] if equal else diff

    def check_results(
            self,
            encoding,
            stdout, expected_stdout,
            stderr, expected_stderr,
            exit_code, expected_exit_code,
            output_files,
            inplace_option=None,
            inplace_inputs=None,
            inplace_content=None):

        """ Compares the various outputs against the expected output.
            Returns [] if everything matched and the comparison output otherwise"""

        result = []
        if exit_code != expected_exit_code:
            result = stderr + ['Ended with unexpected exit code {}. Expected was {}'
                               .format(exit_code, expected_exit_code)]
        else:
            if expected_stdout is not None:
                result.extend(self.check_output(encoding, 'stdout', expected_stdout, stdout))

            if expected_stderr is not None:
                result.extend(self.check_output(encoding, 'stderr', expected_stderr, stderr))

            for (file_name, expected_content) in output_files.items():
                file_name = os.path.join(self.temp_dir, file_name)
                if os.path.exists(file_name):
                    with open(file_name, 'rt', encoding=encoding) as f:
                        file_content = f.read()
                else:
                    file_content = []
                result.extend(self.check_output(encoding, file_name,
                                                expected_content, file_content))

            if inplace_option is not None:
                if type(inplace_inputs) == str or PY2 and type(inplace_inputs) == unicode:
                    inplace_inputs = [inplace_inputs]
                if type(inplace_inputs) != list:
                    raise ValueError('Invalid inplace_inputs list')
                if type(inplace_content) != list:
                    raise ValueError('Invalid inplace_content list')
                if len(inplace_inputs) != len(inplace_content):
                    raise ValueError('List of input files and list of expected edited input ' +
                                     'file content must be of same size')
                inplace_option = make_unicode(inplace_option, encoding)
                for i in range(len(inplace_inputs)):
                    file_name = inplace_inputs[i]
                    if len(inplace_option) > 0:
                        if '*' in inplace_option:
                            bkup_file_name = inplace_option.replace('*',
                                                                    os.path.basename(file_name))
                            if '/' not in bkup_file_name:
                                bkup_file_name = os.path.join(os.path.dirname(file_name),
                                                              bkup_file_name)
                        else:
                            bkup_file_name = file_name+inplace_option
                        if not os.path.exists(bkup_file_name):
                            result.append('Backup file '+bkup_file_name+' is missing!')
                    expected_content = inplace_content[i]
                    if os.path.exists(file_name):
                        with open(file_name, 'rt', encoding=encoding) as f:
                            file_content = f.read()
                    else:
                        file_content = []
                    result.extend(self.check_output(encoding, file_name,
                                                    expected_content, file_content))

        if len(result) > 0:
            try:
                result = '\n'.join(result)
                self.fail(result)
            except TypeError:
                self.fail(str(result))
