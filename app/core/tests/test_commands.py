from unittest.mock import patch
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase


class CommandsTestCase(TestCase):

    def test_wait_for_db_ready(self):
        """Test the function waiting_for_db when db is available"""

        with patch('django.db.utils.ConnectionHandler.__getitem__') as getitem:
            getitem.return_value = True
            call_command('wait_for_db')
            self.assertEqual(getitem.call_count, 1)

    @patch('time.sleep', return_value=None)
    def test_wait_for_db(self, ts):
        """Test the command waiting_for_db"""

        with patch('django.db.utils.ConnectionHandler.__getitem__') as getitem:
            getitem.side_effect = [OperationalError] * 5 + [True]
            call_command('wait_for_db')
            self.assertEqual(getitem.call_count, 6)
