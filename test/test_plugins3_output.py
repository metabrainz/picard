# -*- coding: utf-8 -*-

from io import StringIO

from test.picardtestcase import PicardTestCase

from picard.plugin3.output import PluginOutput


class TestPluginOutput(PicardTestCase):
    def test_print_and_nl(self):
        """Test print and newline methods."""
        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)

        output.print('test message')
        output.nl()
        output.nl(2)

        result = stdout.getvalue()
        self.assertIn('test message', result)
        self.assertEqual(result.count('\n'), 4)  # 1 from print, 1 from nl(), 2 from nl(2)

    def test_warning(self):
        """Test warning output."""
        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)

        output.warning('test warning')

        result = stderr.getvalue()
        self.assertIn('⚠', result)
        self.assertIn('test warning', result)

    def test_warning_with_color(self):
        """Test warning output with color."""
        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=True)

        output.warning('test warning')

        result = stderr.getvalue()
        self.assertIn('\033[33m', result)  # Yellow color code
        self.assertIn('test warning', result)

    def test_auto_color_detection(self):
        """Test automatic color detection from tty."""
        # Mock stdout with isatty
        mock_stdout = StringIO()
        mock_stdout.isatty = lambda: True

        output = PluginOutput(stdout=mock_stdout, stderr=StringIO())
        self.assertTrue(output.color)

        # Mock stdout without isatty
        mock_stdout_no_tty = StringIO()
        mock_stdout_no_tty.isatty = lambda: False

        output_no_color = PluginOutput(stdout=mock_stdout_no_tty, stderr=StringIO())
        self.assertFalse(output_no_color.color)

    def test_error_without_color(self):
        """Test error output without color."""
        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)

        output.error('test error')

        result = stderr.getvalue()
        self.assertIn('✗', result)
        self.assertIn('test error', result)
        self.assertNotIn('\033[', result)  # No color codes

    def test_error_with_color(self):
        """Test error output with color."""
        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=True)

        output.error('test error')

        result = stderr.getvalue()
        self.assertIn('\033[31m', result)  # Red color code
        self.assertIn('test error', result)
