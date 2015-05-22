try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from lighthouse.checks.http import HTTPCheck


@patch("lighthouse.checks.http.client")
class HTTPCheckTests(unittest.TestCase):

    def test_no_dependencies(self, client):
        self.assertEqual(HTTPCheck.validate_dependencies(), True)

    def test_uri_required(self, client):

        HTTPCheck.validate_check_config({"uri": "/foo"})

        self.assertRaises(
            ValueError,
            HTTPCheck.validate_check_config,
            {"foo": "bar"}
        )

    def test_perform_defaults_to_get_method(self, client):
        connection = client.HTTPConnection.return_value
        connection.getresponse.return_value.status = 200

        check = HTTPCheck()
        check.apply_config(
            {
                "host": "localhost", "port": 9999, "uri": "/foo",
                "rise": 1, "fall": 1
            }
        )

        check.perform()

        client.HTTPConnection.assert_called_once_with("localhost", 9999)

        connection = client.HTTPConnection.return_value
        connection.request.assert_called_once_with("GET", "/foo")

        connection.close.assert_called_once_with()

    def test_perform_with_other_method(self, client):
        connection = client.HTTPConnection.return_value
        connection.getresponse.return_value.status = 200

        check = HTTPCheck()
        check.apply_config(
            {
                "host": "localhost", "port": 9999, "uri": "/foo",
                "method": "POST",
                "rise": 1, "fall": 1
            }
        )

        check.perform()

        connection.request.assert_called_once_with("POST", "/foo")

    def test_perform_with_https(self, client):
        connection = client.HTTPSConnection.return_value
        connection.getresponse.return_value.status = 200

        check = HTTPCheck()
        check.apply_config(
            {
                "host": "localhost", "port": 9999, "uri": "/foo",
                "https": True,
                "rise": 1, "fall": 1
            }
        )

        check.perform()

        client.HTTPSConnection.assert_called_once_with("localhost", 9999)

    def test_perform_response_is_200(self, client):
        connection = client.HTTPConnection.return_value
        connection.getresponse.return_value.status = 200

        check = HTTPCheck()
        check.apply_config(
            {
                "host": "localhost", "port": 9999, "uri": "/foo",
                "rise": 1, "fall": 1
            }
        )

        self.assertEqual(check.perform(), True)

    def test_perform_response_is_300(self, client):
        connection = client.HTTPConnection.return_value
        connection.getresponse.return_value.status = 300

        check = HTTPCheck()
        check.apply_config(
            {
                "host": "localhost", "port": 9999, "uri": "/foo",
                "rise": 1, "fall": 1
            }
        )

        self.assertEqual(check.perform(), False)

    def test_perform_response_is_500(self, client):
        connection = client.HTTPConnection.return_value
        connection.getresponse.return_value.status = 500

        check = HTTPCheck()
        check.apply_config(
            {
                "host": "localhost", "port": 9999, "uri": "/foo",
                "rise": 1, "fall": 1
            }
        )

        self.assertEqual(check.perform(), False)

    def test_perform_response_is_404(self, client):
        connection = client.HTTPConnection.return_value
        connection.getresponse.return_value.status = 404

        check = HTTPCheck()
        check.apply_config(
            {
                "host": "localhost", "port": 9999, "uri": "/foo",
                "rise": 1, "fall": 1
            }
        )

        self.assertEqual(check.perform(), False)
