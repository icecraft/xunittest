"""Unittest main program"""

import sys
import os
import types

from . import loader, runner
from .signals import installHandler
from .util import colorStr

__xunittest = True

FAILFAST     = "  -f, --failfast   Stop on first failure\n"
CATCHBREAK   = "  -c, --catch      Catch control-C and display results\n"
BUFFEROUTPUT = "  -b, --buffer     Buffer stdout and stderr during test runs\n"

USAGE_AS_MAIN = """\
Usage: %(progName)s [options] [tests]

Options:
  -h, --help       Show this message
  -v, --verbose    Verbose output
  -q, --quiet      Minimal output
  -i               Enable Interactive Mode
%(failfast)s%(catchbreak)s%(buffer)s
Examples:
  %(progName)s test_module               - run tests from test_module
  %(progName)s module.TestClass          - run tests from module.TestClass
  %(progName)s module.Class.test_method  - run specified test method

[tests] can be a list of any number of test modules, classes and test
methods.

Alternative Usage: %(progName)s discover [options]

Options:
  -v, --verbose    Verbose output
%(failfast)s%(catchbreak)s%(buffer)s  -s directory     Directory to start discovery ('.' default)
  -p pattern       Pattern to match test files ('test*.py' default)
  -t directory     Top level directory of project (default to
                   start directory)

For test discovery all test modules must be importable from the top
level directory of the project.
"""

USAGE_FROM_MODULE = """\
Usage: %(progName)s [options] [test] [...]

Options:
  -h, --help       Show this message
  -v, --verbose    Verbose output
  -q, --quiet      Minimal output
%(failfast)s%(catchbreak)s%(buffer)s
Examples:
  %(progName)s                               - run default set of tests
  %(progName)s MyTestSuite                   - run suite 'MyTestSuite'
  %(progName)s MyTestCase.testSomething      - run MyTestCase.testSomething
  %(progName)s MyTestCase                    - run all 'test*' test methods
                                               in MyTestCase
"""



class TestProgram(object):
    """A command-line program that runs a set of tests; this is primarily
       for making test modules conveniently executable.
    """
    USAGE = USAGE_FROM_MODULE

    # defaults for testing
    failfast = catchbreak = buffer = progName = None

    def __init__(self, module='__main__', defaultTest=None, argv=None,
                    testRunner=None, testLoader=loader.defaultTestLoader,
                    exit=True, verbosity=1, failfast=None, catchbreak=None,
                    buffer=None):
        if isinstance(module, basestring):
            self.module = __import__(module)
            for part in module.split('.')[1:]:
                self.module = getattr(self.module, part)
        else:
            self.module = module
        if argv is None:
            argv = sys.argv

        self.enable_interactive = False
        self.op_by_key = {
            "help":self.interactive_help,
            "exit":self.interactive_exit,
            "test":self.interactive_test,
            "suite":self.interactive_suite,
            "run":self.interactive_run
        } 

        self.exit = exit
        self.failfast = failfast
        self.catchbreak = catchbreak
        self.verbosity = verbosity
        self.buffer = buffer
        self.defaultTest = defaultTest
        self.testRunner = testRunner
        self.testLoader = testLoader
        self.progName = os.path.basename(argv[0])
        self.parseArgs(argv)
        self.runTests()

    def usageExit(self, msg=None):
        if msg:
            print msg
        usage = {'progName': self.progName, 'catchbreak': '', 'failfast': '',
                 'buffer': ''}
        if self.failfast != False:
            usage['failfast'] = FAILFAST
        if self.catchbreak != False:
            usage['catchbreak'] = CATCHBREAK
        if self.buffer != False:
            usage['buffer'] = BUFFEROUTPUT
        print self.USAGE % usage
        sys.exit(2)

    def interactive(self):
        self.enable_interactive = True

    def parseArgs(self, argv):
        if len(argv) > 1 and argv[1].lower() == 'discover':
            self._do_discovery(argv[2:])
            return

        import getopt
        long_opts = ['help', 'verbose', 'quiet', 'failfast', 'catch', 'buffer']
        try:
            options, args = getopt.getopt(argv[1:], 'hHvqfcbiI', long_opts)
            for opt, value in options:
                if opt in ('-h','-H','--help'):
                    self.usageExit()
                if opt in ('-i', '-I'):
                    self.interactive()
                if opt in ('-q','--quiet'):
                    self.verbosity = 0
                if opt in ('-v','--verbose'):
                    self.verbosity = 2
                if opt in ('-f','--failfast'):
                    if self.failfast is None:
                        self.failfast = True
                    # Should this raise an exception if -f is not valid?
                if opt in ('-c','--catch'):
                    if self.catchbreak is None:
                        self.catchbreak = True
                    # Should this raise an exception if -c is not valid?
                if opt in ('-b','--buffer'):
                    if self.buffer is None:
                        self.buffer = True
                    # Should this raise an exception if -b is not valid?
            if len(args) == 0 and self.defaultTest is None:
                # createTests will load tests from self.module
                self.testNames = None
            elif len(args) > 0:
                self.testNames = args
                if __name__ == '__main__':
                    # to support python -m xunittest ...
                    self.module = None
            else:
                self.testNames = (self.defaultTest,)
            self.createTests()
        except getopt.error, msg:
            self.usageExit(msg)

    def createTests(self):
        if self.testNames is None:
            self.test = self.testLoader.loadTestsFromModule(self.module)
        else:
            self.test = self.testLoader.loadTestsFromNames(self.testNames,
                                                           self.module)

    def _do_discovery(self, argv, Loader=None):
        if Loader is None:
            Loader = lambda: self.testLoader

        # handle command line args for test discovery
        self.progName = '%s discover' % self.progName
        import optparse
        parser = optparse.OptionParser()
        parser.prog = self.progName
        parser.add_option('-v', '--verbose', dest='verbose', default=False,
                          help='Verbose output', action='store_true')
        if self.failfast != False:
            parser.add_option('-f', '--failfast', dest='failfast', default=False,
                              help='Stop on first fail or error',
                              action='store_true')
        if self.catchbreak != False:
            parser.add_option('-c', '--catch', dest='catchbreak', default=False,
                              help='Catch ctrl-C and display results so far',
                              action='store_true')
        if self.buffer != False:
            parser.add_option('-b', '--buffer', dest='buffer', default=False,
                              help='Buffer stdout and stderr during tests',
                              action='store_true')
        parser.add_option('-s', '--start-directory', dest='start', default='.',
                          help="Directory to start discovery ('.' default)")
        parser.add_option('-p', '--pattern', dest='pattern', default='test*.py',
                          help="Pattern to match tests ('test*.py' default)")
        parser.add_option('-t', '--top-level-directory', dest='top', default=None,
                          help='Top level directory of project (defaults to start directory)')

        options, args = parser.parse_args(argv)
        if len(args) > 3:
            self.usageExit()

        for name, value in zip(('start', 'pattern', 'top'), args):
            setattr(options, name, value)

        # only set options from the parsing here
        # if they weren't set explicitly in the constructor
        if self.failfast is None:
            self.failfast = options.failfast
        if self.catchbreak is None:
            self.catchbreak = options.catchbreak
        if self.buffer is None:
            self.buffer = options.buffer

        if options.verbose:
            self.verbosity = 2

        start_dir = options.start
        pattern = options.pattern
        top_level_dir = options.top

        loader = Loader()
        self.test = loader.discover(start_dir, pattern, top_level_dir)

    def run_noninteractive(self, testRunner):
        self.result = testRunner.run(self.test)

    def interactive_help(self, keys, testRunner):
        for key in self.op_by_key:
            print " ",key

    def interactive_exit(self, keys, testRunner):
        sys.exit(0)

    def interactive_test(self, keys, testRunner):
        suits = []
        tests_list = []
        for suit in self.test._tests:
            suitName = suit.__repr__().split(" ")[1].split(".")[1]
            suits.append(suitName)
            print suitName
            for test in suit._tests:
                testName = test.__repr__().split(" ")[1].split("=")[1].strip(">")
                if str(test) in test.succTest:
                    print "  {0:50} {1:50}".format( testName, colorStr.greenStr("[ PASSED ]"))
                elif str(test) in test.failTest:
                    print "  {0:50} {1:50}".format( testName, colorStr.redStr("[ FAILED ]"))
                else:
                    print "  {0:50} {1:50}".format( testName, "[ Not Run]")
                
    def interactive_suite(self, keys, testRunner):
        for suit in self.test._tests:
                print str(suit).split()[1].split(".")[1]

            
    def interactive_run(self, keys, testRunner):
	try:
      	  runFilterStr = keys[0]
	except IndexError :
	  runFilterStr = "all"

        for suit in self.test._tests:
            suitName = suit.__repr__().split(" ")[1].split(".")[1]
            for test in suit._tests:
                test.runFilterStr = runFilterStr
                
        self.result = testRunner.run(self.test)


    def parse_process_interactive(self, input, testRunner):
        keys = []
        for key in input.split(" "):
            if len(key) > 0:
                keys.append(key)
        if not keys:
            return
        try:
            self.op_by_key.get(keys[0])(keys[1:], testRunner)
        except TypeError as e:
           self.input_prompt()

    def prompt_nextLine(self):
        sys.stdout.write("\n")
    def input_prompt(self):
        sys.stdout.write( ">>>>")
        
    def run_interactive(self, testRunner):
        stdin = sys.stdin
        while True:
            self.prompt_nextLine()
            self.input_prompt()
            inputStr = stdin.readline().strip("\n")
            self.parse_process_interactive(inputStr, testRunner)

    def runTests(self):
        if self.catchbreak:
            installHandler()
        if self.testRunner is None:
            self.testRunner = runner.TextTestRunner
        if isinstance(self.testRunner, (type, types.ClassType)):
            try:
                testRunner = self.testRunner(verbosity=self.verbosity,
                                             failfast=self.failfast,
                                             buffer=self.buffer)
            except TypeError:
                # didn't accept the verbosity, buffer or failfast arguments
                testRunner = self.testRunner()
        else:
            # it is assumed to be a TestRunner instance
            testRunner = self.testRunner

        if self.enable_interactive == True:
            self.run_interactive(testRunner)
        else :
            self.run_noninteractive(testRunner)

        if self.exit:
            sys.exit(not self.result.wasSuccessful())



main = TestProgram
