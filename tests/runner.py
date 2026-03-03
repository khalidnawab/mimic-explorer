"""
Custom test runner for mimic-explorer --test.
Shows user-friendly pass/fail output with descriptions.
"""
import logging
import sys
import unittest
import warnings
from django.test.runner import DiscoverRunner


class FriendlyTestResult(unittest.TextTestResult):
    """Test result that shows readable descriptions for each test."""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.successes = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(test)
        doc = test.shortDescription() or str(test)
        self.stream.write(f'  PASS  {doc}\n')
        self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        doc = test.shortDescription() or str(test)
        self.stream.write(f'  FAIL  {doc}\n')
        # Print the failure message (the helpful msg= text)
        tb_text = self._exc_info_to_string(err, test)
        # Extract just the AssertionError message, not the full traceback
        for line in tb_text.strip().split('\n'):
            if line.startswith('AssertionError') or line.startswith('AssertionError:'):
                self.stream.write(f'        {line}\n')
                break
        else:
            # Fallback: show last line of traceback
            last_line = tb_text.strip().split('\n')[-1]
            self.stream.write(f'        {last_line}\n')
        self.stream.write('\n')
        self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        doc = test.shortDescription() or str(test)
        self.stream.write(f'  ERROR {doc}\n')
        tb_text = self._exc_info_to_string(err, test)
        last_line = tb_text.strip().split('\n')[-1]
        self.stream.write(f'        {last_line}\n\n')
        self.stream.flush()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        doc = test.shortDescription() or str(test)
        self.stream.write(f'  SKIP  {doc}\n')
        self.stream.write(f'        Reason: {reason}\n')
        self.stream.flush()

    def printErrors(self):
        # Only print detailed tracebacks for failures/errors
        if self.failures or self.errors:
            self.stream.write('\n' + '=' * 60 + '\n')
            self.stream.write('DETAILED FAILURE/ERROR INFO:\n')
            self.stream.write('=' * 60 + '\n')
            super().printErrors()


class FriendlyTestRunner(unittest.TextTestRunner):
    """Test runner that uses FriendlyTestResult."""
    resultclass = FriendlyTestResult

    def run(self, test):
        self.stream.write('\n')
        self.stream.write('  MIMIC Explorer Test Suite\n')
        self.stream.write('  ' + '=' * 40 + '\n\n')

        # Run the tests — collect results without the default summary
        result = self._makeResult()
        test(result)

        # Print detailed failure tracebacks if any
        result.printErrors()

        # Print our clean summary
        self.stream.write('\n  ' + '-' * 40 + '\n')
        total = result.testsRun
        passed = len(result.successes)
        failed = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)

        self.stream.write(f'  Results: {passed} passed')
        if failed:
            self.stream.write(f', {failed} failed')
        if errors:
            self.stream.write(f', {errors} errors')
        if skipped:
            self.stream.write(f', {skipped} skipped')
        self.stream.write(f' ({total} total)\n')

        if failed == 0 and errors == 0:
            self.stream.write('  All tests passed! Your installation is working correctly.\n')
        else:
            self.stream.write('\n  Some tests failed. Read the messages above for details\n')
            self.stream.write('  on what went wrong and where to look to fix it.\n')

        self.stream.write('\n')
        return result


class MIMICTestRunner(DiscoverRunner):
    """Django test runner that suppresses migrations noise and uses friendly output."""

    def __init__(self, **kwargs):
        kwargs['verbosity'] = 0  # Suppress migration output
        super().__init__(**kwargs)

    def get_resultclass(self):
        return FriendlyTestResult

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        # Suppress noisy warnings that clutter test output
        warnings.filterwarnings('ignore', message='.*naive datetime.*', category=RuntimeWarning)
        # Suppress SQLite threading noise from background-thread import tests
        logging.getLogger('django.db.backends').setLevel(logging.CRITICAL)
        # Suppress unhandled thread exception tracebacks (e.g. SQLite lock in
        # background import thread tests — the test itself handles the outcome)
        import threading
        threading.excepthook = lambda args: None

    def run_suite(self, suite, **kwargs):
        runner = FriendlyTestRunner(
            stream=sys.stderr,
            verbosity=0,
        )
        return runner.run(suite)
