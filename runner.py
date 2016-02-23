"""Running tests"""

import sys
import time

from . import result
from .signals import registerResult
from .util import colorStr 

__xunittest = True


class _WritelnDecorator(object):
    """Used to decorate file-like objects with a handy 'writeln' method"""
    def __init__(self,stream):
        self.stream = stream

    def __getattr__(self, attr):
        if attr in ('stream', '__getstate__'):
            raise AttributeError(attr)
        return getattr(self.stream,attr)

    def writeln(self, arg=None):
        if arg:
            self.write(arg)
        self.write('\n') # text-mode streams translate to \r\n if needed

    def writeStr(self, arg):
        self.write(arg)
                   
    def red(self, s):
        self.write( colorStr.redStr(s))
        
    def green(self, s):
        self.write( colorStr.greenStr(s))
    
    
    
class TextTestResult(result.TestResult):
    """A test result class that can print formatted text results to a stream.

    Used by TextTestRunner.
    """
    separator1 = '=' * 70
    separator2 = '-' * 70

    def __init__(self, stream, descriptions, verbosity):
        super(TextTestResult, self).__init__(stream, descriptions, verbosity)
        self.stream = stream
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.descriptions = descriptions

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return '\n'.join((str(test), doc_first_line))
        else:
            return str(test)

    def startTest(self, test):
        super(TextTestResult, self).startTest(test)
        if self.showAll:
            self.stream.write(self.getDescription(test))
            self.stream.write(" ... ")
            self.stream.flush()

    def addSuccess(self, test):
        super(TextTestResult, self).addSuccess(test)
        self.resultRecord = colorStr.greenStr("[ PASSED ]")
        self.stream.writeStr("{0:30} {1:30}".format(self.resultRecord, " "*30))
        self.stream.writeln(self.getDescription(test))
        
        if str(test) in test.failTest:
            test.failTest.remove(str(test))
        if str(test) not in test.succTest:
            test.succTest.append(str(test))



    def addError(self, test, err):
        self.resultRecord = colorStr.redStr("[ ERROR  ]")
        super(TextTestResult, self).addError(test, err)
        self.stream.writeStr("{0:30} {1:30}".format(self.resultRecord, " "*30))
        self.stream.writeln(self.getDescription(test))
        self.stream.write(self._exc_info_to_string(err, test))
        if str(test) in test.succTest:
            test.succTest.remove(str(test))
        if str(test) not in test.failTest:
            test.failTest.append(str(test))


    def addFailure(self, test, err):
        self.resultRecord = colorStr.redStr("[ FAILED ]")
        super(TextTestResult, self).addFailure(test, err)
        self.stream.writeStr("{0:30} {1:30}".format(self.resultRecord, " "*30))
        self.stream.writeln(self.getDescription(test))
        self.stream.write(self._exc_info_to_string(err, test))
        if not str(test) in test.failTest:
            test.failTest.append(str(test))
        if str(test)  in test.succTest:
            test.succTest.remove(str(test))


    def addSkip(self, test, reason):
        super(TextTestResult, self).addSkip(test, reason)
        if self.showAll:
            self.stream.writeln("skipped {0!r}".format(reason))
        elif self.dots:
            self.stream.write("s")
            self.stream.flush()

    def addExpectedFailure(self, test, err):
        super(TextTestResult, self).addExpectedFailure(test, err)
        if self.showAll:
            self.stream.writeln("expected failure")
        elif self.dots:
            self.stream.write("x")
            self.stream.flush()

    def addUnexpectedSuccess(self, test):
        super(TextTestResult, self).addUnexpectedSuccess(test)
        if self.showAll:
            self.stream.writeln("unexpected success")
        elif self.dots:
            self.stream.write("u")
            self.stream.flush()

    def printErrors(self):
        return
        """
        if self.dots or self.showAll:
            self.stream.writeln()
        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)
        """

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour,self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)


class TextTestRunner(object):
    """A test runner class that displays results in textual form.

    It prints out the names of tests as they are run, errors as they
    occur, and a summary of the results at the end of the test run.
    """
    resultclass = TextTestResult

    def __init__(self, stream=sys.stderr, descriptions=True, verbosity=1,
                 failfast=False, buffer=False, resultclass=None):
        self.stream = _WritelnDecorator(stream)
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        if resultclass is not None:
            self.resultclass = resultclass

    def _makeResult(self):
        return self.resultclass(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        startTime = time.time()
        startTestRun = getattr(result, 'startTestRun', None)
        if startTestRun is not None:
            startTestRun()
        try:
            test(result)
        finally:
            stopTestRun = getattr(result, 'stopTestRun', None)
            if stopTestRun is not None:
                stopTestRun()
        stopTime = time.time()
        timeTaken = stopTime - startTime
        result.printErrors()
        if hasattr(result, 'separator2'):
            self.stream.writeln(result.separator2)
        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()

        expectedFails = unexpectedSuccesses = skipped = 0
        try:
            results = map(len, (result.expectedFailures,
                                result.unexpectedSuccesses,
                                result.skipped))
        except AttributeError:
            pass
        else:
            expectedFails, unexpectedSuccesses, skipped = results

        infos = []
        if not result.wasSuccessful():
            self.stream.write("[FAILED]")
            failed, errored = map(len, (result.failures, result.errors))
            if failed:
                infos.append("failures=%d" % failed)
            if errored:
                infos.append("errors=%d" % errored)
        else:
            self.stream.write("OK")
        if skipped:
            infos.append("skipped=%d" % skipped)
        if expectedFails:
            infos.append("expected failures=%d" % expectedFails)
        if unexpectedSuccesses:
            infos.append("unexpected successes=%d" % unexpectedSuccesses)
        if infos:
            self.stream.writeln(" (%s)" % (", ".join(infos),))
        else:
            self.stream.write("\n")
        return result
