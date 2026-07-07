import os

os.environ.setdefault('AWS_EXECUTION_ENV', 'CI')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

import unittest

from application import app


class StaticPageSmokeTests(unittest.TestCase):
    """These routes render a template with no DynamoDB/MySQL calls, so they're
    safe to hit without live AWS credentials."""

    def setUp(self):
        self.client = app.test_client()

    def test_static_pages_return_200(self):
        for path in ('/syntax', '/api', '/feedback', '/resources'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
