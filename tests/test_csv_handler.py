import unittest
import tempfile

from coinbasis.csv_handler import (
    parse_float,
    parse_string,
    parse_row,
    parse_csv,
    get_field_parser,
    transaction_to_row,
    write_csv,
    csv,
    Transaction,
    COLUMN_MAP,
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


class TestParseCSV(unittest.TestCase):
    def test_parse_csv_basic(self):
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w+', newline='', delete=False) as tmp:
            writer = csv.writer(tmp)
            writer.writerow(['Date', 'Type', 'Transaction ID', 'Received Quantity', 'Received Currency'])
            writer.writerow(['2024-01-01 12:00:00', 'STAKING_REWARD', '12345', '1.23', 'ATOM'])
            writer.writerow(['2024-01-02 13:00:00', 'INTEREST_PAYMENT', '67890', '2.50', 'BTC'])
            tmp_path = tmp.name

        transactions = parse_csv(tmp_path)

        self.assertEqual(len(transactions), 2)
        self.assertIsInstance(transactions[0], Transaction)

        # Validate first row
        t1 = transactions[0]
        self.assertEqual(t1.timestamp, '2024-01-01 12:00:00')
        self.assertEqual(t1.type, 'STAKING_REWARD')
        self.assertEqual(t1.transaction_id, '12345')
        self.assertEqual(t1.received_qty, 1.23)
        self.assertEqual(t1.received_currency, 'ATOM')

        # Validate second row
        t2 = transactions[1]
        self.assertEqual(t2.timestamp, '2024-01-02 13:00:00')
        self.assertEqual(t2.type, 'INTEREST_PAYMENT')
        self.assertEqual(t2.transaction_id, '67890')
        self.assertEqual(t2.received_qty, 2.50)
        self.assertEqual(t2.received_currency, 'BTC')

    def test_parse_csv_missing_fields(self):
        with tempfile.NamedTemporaryFile(mode='w+', newline='', delete=False) as tmp:
            writer = csv.writer(tmp)
            writer.writerow(['Date', 'Type', 'Transaction ID', 'Received Quantity', 'Received Currency'])
            writer.writerow(['2024-01-01', '12345', 'STAKING_REWARD', '', ''])
            tmp_path = tmp.name

        transactions = parse_csv(tmp_path)
        t = transactions[0]

        self.assertIsNone(t.received_qty)
        self.assertIsNone(t.received_currency)

    def test_parse_csv_ignores_unknown_columns(self):
        with tempfile.NamedTemporaryFile(mode='w+', newline='', delete=False) as tmp:
            writer = csv.writer(tmp)
            writer.writerow(['Date', 'Type', 'Transaction ID', 'Unknown Column'])
            writer.writerow(['2024-01-01', 'STAKING_REWARD', '12345', 'ignored'])
            tmp_path = tmp.name

        transactions = parse_csv(tmp_path)
        t = transactions[0]

        self.assertEqual(t.timestamp, '2024-01-01')
        self.assertEqual(t.type, 'STAKING_REWARD')
        self.assertEqual(t.transaction_id, '12345')

    def test_parse_csv_empty(self):
        with tempfile.NamedTemporaryFile(mode='w+', newline='', delete=False) as tmp:
            writer = csv.writer(tmp)
            writer.writerow(['Date', 'Type', 'Transaction ID'])  # header only
            tmp_path = tmp.name

        transactions = parse_csv(tmp_path)
        self.assertEqual(transactions, [])


class TestTransactionToRow(unittest.TestCase):
    def test_transaction_to_row_basic(self):
        tx = Transaction(
            timestamp='2024-01-01 12:00:00',
            type='STAKING_REWARD',
            transaction_id='12345',
            received_qty=1.23,
            received_currency='ATOM'
        )

        row = transaction_to_row(tx)

        self.assertEqual(set(row.keys()), set(COLUMN_MAP.keys()))
        self.assertEqual(row['Date'], '2024-01-01 12:00:00')
        self.assertEqual(row['Type'], 'STAKING_REWARD')
        self.assertEqual(row['Transaction ID'], '12345')
        self.assertEqual(row['Received Quantity'], '1.23')
        self.assertEqual(row['Received Currency'], 'ATOM')

    def test_transaction_to_row_none_values(self):
        tx = Transaction(
            timestamp='2024-01-01',
            type='INTEREST_PAYMENT',
            transaction_id='abc123',
            received_qty=None,
            received_currency=None
        )

        row = transaction_to_row(tx)

        self.assertEqual(row['Received Quantity'], '')
        self.assertEqual(row['Received Currency'], '')

    def test_transaction_to_row_float_format(self):
        tx = Transaction(
            timestamp='2024-01-01',
            type='INTEREST_PAYMENT',
            transaction_id='xyz',
            received_qty=0.00012345
        )

        row = transaction_to_row(tx)

        self.assertEqual(row['Received Quantity'], '0.00012345')

    def test_transaction_to_row_column_order(self):
        tx = Transaction(
            timestamp='2024-01-01',
            type='INTEREST_PAYMENT',
            transaction_id='xyz'
        )

        row = transaction_to_row(tx)

        # DictWriter relies on COLUMN_MAP order
        expected_order = list(COLUMN_MAP.keys())
        actual_order = list(row.keys())

        self.assertEqual(actual_order, expected_order)


class TestWriteCSV(unittest.TestCase):

    def test_write_csv_basic(self):
        tx1 = Transaction(
            timestamp='2024-01-01 12:00:00',
            type='STAKING_REWARD',
            transaction_id='12345',
            received_qty=1.23,
            received_currency='ATOM'
        )

        tx2 = Transaction(
            timestamp='2024-01-02 13:00:00',
            type='INTEREST_PAYMENT',
            transaction_id='67890',
            received_qty=2.50,
            received_currency='BTC'
        )

        with tempfile.NamedTemporaryFile(mode='w+', newline='', delete=False) as tmp:
            tmp_path = tmp.name

        write_csv(tmp_path, [tx1, tx2])

        # Read back the file
        with open(tmp_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        self.assertEqual(len(rows), 2)

        # Validate first row
        r1 = rows[0]
        self.assertEqual(r1['Date'], '2024-01-01 12:00:00')
        self.assertEqual(r1['Type'], 'STAKING_REWARD')
        self.assertEqual(r1['Transaction ID'], '12345')
        self.assertEqual(r1['Received Quantity'], '1.23')
        self.assertEqual(r1['Received Currency'], 'ATOM')

        # Validate second row
        r2 = rows[1]
        self.assertEqual(r2['Date'], '2024-01-02 13:00:00')
        self.assertEqual(r2['Type'], 'INTEREST_PAYMENT')
        self.assertEqual(r2['Transaction ID'], '67890')
        self.assertEqual(r2['Received Quantity'], '2.5')
        self.assertEqual(r2['Received Currency'], 'BTC')

    def test_write_csv_none_values(self):
        tx = Transaction(
            timestamp='2024-01-01',
            type='INTEREST_PAYMENT',
            transaction_id='abc123',
            received_qty=None,
            received_currency=None
        )

        with tempfile.NamedTemporaryFile(mode='w+', newline='', delete=False) as tmp:
            tmp_path = tmp.name

        write_csv(tmp_path, [tx])

        with open(tmp_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            row = next(reader)

        self.assertEqual(row['Received Quantity'], '')
        self.assertEqual(row['Received Currency'], '')

    def test_write_csv_header_order(self):
        tx = Transaction(
            timestamp='2024-01-01',
            type='INTEREST_PAYMENT',
            transaction_id='xyz'
        )

        with tempfile.NamedTemporaryFile(mode='w+', newline='', delete=False) as tmp:
            tmp_path = tmp.name

        write_csv(tmp_path, [tx])

        with open(tmp_path, newline='') as csvfile:
            header = csvfile.readline().strip().split(',')

        expected = list(COLUMN_MAP.keys())
        self.assertEqual(header, expected)

    def test_write_csv_empty_list(self):
        with tempfile.NamedTemporaryFile(mode='w+', newline='', delete=False) as tmp:
            tmp_path = tmp.name

        write_csv(tmp_path, [])

        with open(tmp_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        # No rows, but header exists
        self.assertEqual(rows, [])
        self.assertEqual(reader.fieldnames, list(COLUMN_MAP.keys()))
