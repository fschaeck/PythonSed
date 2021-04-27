# -*- coding: utf-8 -*-
"""Utility for PythonSed unittest testcases"""
import logging
import os
import sys
import tempfile
import unittest

import PythonSed

PY2 = False
PY3 = False
if sys.version_info[0] == 2:
    PY2 = True
    from StringIO import StringIO
else:
    PY3 = True
    from io import open as open
    from io import StringIO
    OPEN_ARGS = {'encoding': 'latin-1'}

ON_TRAVIS = "TRAVIS" in os.environ


class Redirecting(list):
    def __init__(self, stdin_data):
        self._stdin_data = stdin_data
        self._stdin = None

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio_out = StringIO()
        if self._stdin_data is not None:
            self._stdin = sys.stdin
            sys.stdin = self._stringio_in = StringIO(self._stdin_data)
        else:
            self._stdin = None
        return self

    def __exit__(self, **args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout
        del self._stringio_out
        if self._stdin is not None:
            del self._stringio_in
            sys.stdin = self._stdin


class PythonSedTestCase(unittest.TestCase):
    """A test case implementing utility methods for testing PythonSed"""

    maxDiff = 4096  # max diff size

    environment = {}

    TEST_FILE_STEM = 'sed-test-{inoutscript}.{ext}'

    def get_data_path(self):
        """return the data/ sibling path"""
        curpath = os.path.dirname(sys.modules[self.__module__].__file__)
        return os.path.abspath(os.path.join(curpath, "data"))

    def setUp(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.debug(u"preparing environment...")
        for kn in self.environment:
            if kn not in os.environ:
                v = self.environment[kn]
                self.logger.debug(u"Setting $" + str(kn) + " to: " + repr(v))
                os.environ[kn] = v

        self.logger.debug(u"preparing sys.path...")
        testpath = os.path.abspath(os.path.dirname(sys.modules[self.__module__].__file__))
        if testpath not in sys.path:
            sys.path.append(testpath)

        self.cwd = testpath
        self.logger.info(u"Target CWD is: " + str(self.cwd))
        if self.cwd != os.getcwd():
            os.chdir(self.cwd)
        self.logger.debug(u"After cd, CWD is: " + os.getcwd())

    def tearDown(self):
        pass

    def run_test(self,
                 mode,                 # 0=run PythonSed.main(), 1=use PythonSed object
                 scripts=[],           # literal script strings (-e options)
                 files=[],             # script file names (-f options)
                 stdin=None,           # stdin input to command
                 inplace=None,         # None=no inplace editing
                                       # ''=inplace editing without backup
                                       # '.suffix'=backup to <filename>.suffix
                                       # 'xxx/yyy_*/*.zzz'= backup to
                                       #     xxx/yyy_<filename>/<filename>.zzz
                 no_autoprint=False,   # do not print anyhing automatically
                 separate=False,       # process input files separately instead of continous stream
                 python_syntax=False,  # use python syntax for regex
                 extended=False,       # use extended regex syntax (-E option)
                 line_length=70,       # default line length for l command
                 debug=0,              # debug level (0..3)
                 input_files={},       # content of files read by the sed script
                 stdout=None,          # expected output to stdout
                 output_files={},      # expected content of files written by the sed script
                 ):
        pass

    def get_file_name(self, name, extension, index=None):
        file_name = name
        if index is not None:
            file_name += '.'+str(index)
        file_name += '.'+extension
        return os.path.join(os.getcwd(), file_name)

    def get_file_content(self, name, extension, index=None):
        filename = self.get_file_name(name, extension, index)
        if os.path.exists(filename):
            with open(filename, 'rt', **OPEN_ARGS) as f:
                content = f.read()
            return content
        else:
            return None

    def get_file_lines(self, name, extension, index=None):
        content = self.get_file_content(name, extension, index)
        if content is None:
            return None
        else:
            return content.split('\n')

    def run_test_from_files(self, name):
        options = self.get_file_lines(name, 'options')
        stdin = self.get_file_content(name, 'stdin')
        stdout = self.get_file_lines(name, 'stdout')
        output_files = {}
        for i in range(3):
            content = self.get_file_content(name, 'out.result', index=i)
            if content is not None:
                output_files[self.get_file_name(name, 'out', index=i)] = content
            else:
                break
        args = ['sed.py']+options+['-f', self.get_file_name(name, 'sed')]
        for i in range(3):
            file_name = self.get_file_name(name, 'in', index=i)
            if os.path.exists(file_name):
                args.append(file_name)

        sys.argv = args
        with Redirecting(stdin) as output:
            exit_code = PythonSed.sed.main()

        if stdout is None and exit_code != 0:
            return 0
        else 

    def do_test(self, cmd, cmp_str, ensure_same_cwd=True, ensure_undefined=(), ensure_defined=(), exitcode=None):

        saved_cwd = os.getcwd()
        self.logger.info(u"executing {c} in {d}...".format(c=cmd, d=saved_cwd))
        # 1 for mimicking running from console
        worker = self.stash(cmd, persistent_level=1)

        self.assertEqual(cmp_str, self.stash.main_screen.text, u'output not identical')

        if exitcode is not None:
            self.assertEqual(worker.state.return_value, exitcode, u"unexpected exitcode")
        else:
            self.logger.info(u"Exitcode: " + str(worker.state.return_value))

        if ensure_same_cwd:
            assert os.getcwd() == saved_cwd, 'cwd changed'
        else:
            if os.getcwd() != saved_cwd:
                self.logger.warning(u"CWD changed from '{o}' to '{n}'!".format(o=saved_cwd, n=os.getcwd()))

        for v in ensure_undefined:
            assert v not in self.stash.runtime.state.environ.keys(), u'%s should be undefined' % v

        for v in ensure_defined:
            assert v in self.stash.runtime.state.environ.keys(), u'%s should be defined' % v

    def run_command(self, command, exitcode=None):
        """
        Run a command and return its output.
        :param command: command to run
        :type command: str
        :param exitcode: expected exitcode, None to ignore
        :type exitcode: int or None
        :return: output of the command
        :rtype: str
        """
        # for debug purposes, locate script
        try:
            scriptname = command.split(" ")[0]
            scriptfile = self.stash.runtime.find_script_file(scriptname)
            self.logger.debug(u"Scriptfile for command: " + str(scriptfile))
        except Exception as e:
            self.logger.warning(u"Could not find script for command: " + repr(e))
            # do NOT return here, script may be alias
        outs = StringIO()
        self.logger.info(u"Executing: " + repr(command))
        worker = self.stash(
            command,
            persistent_level=1,
            final_outs=outs,
            final_errs=outs,
            cwd=self.cwd
        )  # 1 for mimicking running from console
        output = outs.getvalue()
        returnvalue = worker.state.return_value
        self.logger.debug(output)
        self.logger.debug("Exitcode: " + str(returnvalue))
        if exitcode is not None:
            self.assertEqual(
                returnvalue,
                exitcode,
                u"unexpected exitcode ({e} expected, got {g})\nOutput:\n{o}\n".format(e=exitcode,
                                                                                      g=returnvalue,
                                                                                      o=output),
            )
        return output
