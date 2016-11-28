import os
import logging
import datetime
from unittest import TestCase

os.environ['REDASH_REDIS_URL'] = "redis://localhost:6379/5"
# Use different url for Celery to avoid DB being cleaned up:
os.environ['REDASH_CELERY_BROKER'] = "redis://localhost:6379/6"

# Dummy values for oauth login
os.environ['REDASH_GOOGLE_CLIENT_ID'] = "dummy"
os.environ['REDASH_GOOGLE_CLIENT_SECRET'] = "dummy"
os.environ['REDASH_MULTI_ORG'] = "true"

import redash.models
from redash import create_app
from redash import redis_connection
from factories import Factory
from tests.handlers import make_request

logging.disable("INFO")
logging.getLogger("metrics").setLevel("ERROR")


class BaseTestCase(TestCase):
    def setUp(self):
        redash.models.db.session.close()
        self.app = create_app()
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        redash.models.create_db(True, True)
        self.factory = Factory()

    def tearDown(self):
        redash.models.create_db(False, True)
        self.app_ctx.pop()
        redis_connection.flushdb()

    def make_request(self, method, path, org=None, user=None, data=None, is_json=True):
        if user is None:
            user = self.factory.user

        if org is None:
            org = self.factory.org

        if org is not False:
            path = "/{}{}".format(org.slug, path)

        return make_request(method, path, user, data, is_json)

    def assertResponseEqual(self, expected, actual):
        for k, v in expected.iteritems():
            if isinstance(v, datetime.datetime) or isinstance(actual[k], datetime.datetime):
                continue

            if isinstance(v, list):
                continue

            if isinstance(v, dict):
                self.assertResponseEqual(v, actual[k])
                continue

            self.assertEqual(v, actual[k], "{} not equal (expected: {}, actual: {}).".format(k, v, actual[k]))
