# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from tornado.testing import gen_test

from tests.base import TestCase
from thumbor.config import Config
from thumbor.importer import Importer


def assert_expires_in(headers, seconds):
    """Checks the Expires header really lands `seconds` from now.

    The value used to be built from datetime.utcnow(), which is naive;
    tornado converts an aware datetime to UTC before formatting, so the
    header is unchanged -- this asserts that rather than assuming it.
    """

    expires = parsedate_to_datetime(headers["Expires"])

    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    expected = datetime.now(timezone.utc) + timedelta(seconds=seconds)

    assert (
        abs((expires - expected).total_seconds()) < 60
    ), f"Expires is {expires}, expected around {expected}"


class BaseMaxAgeFilterTestCase(TestCase):
    def get_fixture_path(self, name):
        return f"./tests/fixtures/{name}"

    def get_config(self):
        return Config.load(self.get_fixture_path("max_age_conf.py"))

    def get_importer(self):
        importer = Importer(self.config)
        importer.import_modules()
        return importer


class MaxAgeFilterTestCase(BaseMaxAgeFilterTestCase):
    @gen_test
    async def test_max_age_filter_with_regular_image(self):
        response = await self.async_fetch(
            "/unsafe/smart/image.jpg", method="GET"
        )
        assert response.code == 200
        assert response.headers["Cache-Control"] == "max-age=2,public"
        assert_expires_in(response.headers, 2)

    @gen_test
    async def test_max_age_url(self):
        response = await self.async_fetch(
            "/unsafe/filters:max_age(30)/image.jpg", method="GET"
        )
        assert response.code == 200
        assert response.headers["Cache-Control"] == "max-age=30,public"
        assert_expires_in(response.headers, 30)


class MaxAgeDetectorFilterTestCase(BaseMaxAgeFilterTestCase):
    def get_config(self):
        config = super().get_config()
        config.DETECTORS = ["tests.fixtures.prevent_result_storage_detector"]
        return config

    @gen_test
    async def test_max_age_filter_with_non_storaged_image(self):
        response = await self.async_fetch(
            "/unsafe/smart/image.jpg", method="GET"
        )
        assert response.code == 200
        assert response.headers["Cache-Control"] == "max-age=1,public"
        assert "Expires" in response.headers


class MaxAgeErrorDectectorFilterTestCase(BaseMaxAgeFilterTestCase):
    def get_config(self):
        config = super().get_config()
        config.DETECTORS = ["tests.fixtures.detection_error_detector"]
        return config

    @gen_test
    async def test_with_detection_error_image(self):
        response = await self.async_fetch(
            "/unsafe/smart/image.jpg", method="GET"
        )
        assert response.code == 200
        assert response.headers["Cache-Control"] == "max-age=1,public"
        assert "Expires" in response.headers
