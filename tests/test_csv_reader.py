import unittest

from coinbasis.csv_reader import (
    parse_float,
    parse_string,
    parse_row,
    parse_csv,
    get_field_parser,
)


class TestParseFloat(unittest.TestCase):
    def test_parse_float_valid(self):
        self.assertEqual(parse_float('1.23'), 1.23)
        self.assertEqual(parse_float('  4.56  '), 4.56)

    def test_parse_float_blank(self):
        self.assertEqual(parse_float(''), None)
        self.assertEqual(parse_float('   '), None)

    def test_parse_float_ellipsis(self):
        self.assertEqual(parse_float('...'), None)

    def test_parse_float_zero(self):
        self.assertEqual(parse_float('0'), 0.0)


class TestParseString(unittest.TestCase):
    def test_parse_string_valid(self):
        self.assertEqual(parse_string('hello'), 'hello')
        self.assertEqual(parse_string('  world  '), 'world')

    def test_parse_string_blank(self):
        self.assertEqual(parse_string(''), None)
        self.assertEqual(parse_string('   '), None)

    def test_parse_string_ellipsis(self):
        self.assertEqual(parse_string('...'), None)

    def test_parse_string_numeric_like(self):
        self.assertEqual(parse_string('123'), '123')


class TestGetFieldParser(unittest.TestCase):
    def test_float_field_returns_parse_float(self):
        parser = get_field_parser('received_qty')
        self.assertIs(parser, parse_float)

    def test_float_union_field_returns_parse_float(self):
        parser = get_field_parser('received_usd_cost_basis')
        self.assertIs(parser, parse_float)

    def test_string_field_returns_parse_string(self):
        parser = get_field_parser('received_currency')
        self.assertIs(parser, parse_string)

    def test_string_union_field_returns_parse_string(self):
        parser = get_field_parser('received_wallet')
        self.assertIs(parser, parse_string)


class TestParseRow(unittest.TestCase):
    def test_parse_row_basic_mapping(self):
        row = {
            'Date': '2024-01-01 12:00:00',
            'Type': 'STAKING_REWARD',
            'Received Quantity': '1.23',
            'Received Currency': 'ATOM',
        }
        parsed = parse_row(row)

        self.assertIn('timestamp', parsed)
        self.assertIn('type', parsed)
        self.assertIn('received_qty', parsed)
        self.assertIn('received_currency', parsed)

        self.assertEqual(parsed['timestamp'], '2024-01-01 12:00:00')
        self.assertEqual(parsed['type'], 'STAKING_REWARD')
        self.assertEqual(parsed['received_qty'], 1.23)
        self.assertEqual(parsed['received_currency'], 'ATOM')

    def test_parse_row_ignores_unknown_columns(self):
        row = {
            'Date': '2024-01-01',
            'Unknown Column': 'should be ignored',
        }
        parsed = parse_row(row)

        self.assertEqual(len(parsed), 1)
        self.assertIn('timestamp', parsed)
        self.assertNotIn('Unknown Column', parsed)

    def test_parse_row_handles_blank_values(self):
        row = {
            'Received Quantity': '',
            'Received Currency': '   ',
        }
        parsed = parse_row(row)

        self.assertIsNone(parsed['received_qty'])
        self.assertIsNone(parsed['received_currency'])

    def test_parse_row_uses_correct_parser(self):
        row = {
            'Received Quantity': '2.5',
            'Received Currency': 'BTC',
        }
        parsed = parse_row(row)

        self.assertIsInstance(parsed['received_qty'], float)
        self.assertIsInstance(parsed['received_currency'], str)