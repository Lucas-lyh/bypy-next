"""Offline tests for direct Baidu OAuth; no real credentials or requests."""
import unittest
from unittest.mock import Mock, patch

from bypy import ByPy, const


class DirectAuthTests(unittest.TestCase):
    def client(self):
        client = object.__new__(ByPy)
        client._apikey = 'test-app-key'
        client._secretkey = 'test-app-secret'
        client._timeout = 30
        client._json = {'refresh_token': 'test-refresh-token'}
        client.pd = Mock()
        client._post = Mock(return_value=const.ENoError)
        return client

    def test_authorization_exchanges_code_directly_with_baidu(self):
        client = self.client()
        with patch('bypy.bypy.ask', return_value='test-authorization-code') as ask, patch('bypy.bypy.pr'):
            self.assertEqual(client._auth(), const.ENoError)
        self.assertIn(const.AuthorizationUrl, ask.call_args[0][0])
        client._post.assert_called_once_with(
            const.TokenUrl,
            {'grant_type': 'authorization_code', 'code': 'test-authorization-code',
             'client_id': 'test-app-key', 'client_secret': 'test-app-secret',
             'redirect_uri': 'oob'}, client._auth_act, addtoken=False)

    def test_refresh_does_not_attach_expired_access_token(self):
        client = self.client()
        self.assertEqual(client._refresh_token(), const.ENoError)
        client._post.assert_called_once_with(
            const.TokenUrl,
            {'grant_type': 'refresh_token', 'refresh_token': 'test-refresh-token',
             'client_id': 'test-app-key', 'client_secret': 'test-app-secret'},
            client._refresh_token_act, addtoken=False)

    def test_refresh_failure_is_returned(self):
        client = self.client()
        client._post.return_value = const.ERequestFailed
        self.assertEqual(client._refresh_token(), const.ERequestFailed)
        client._post.assert_called_once()

    def test_token_responses_are_saved_by_existing_storage(self):
        client = self.client()
        client._store_json = Mock(return_value=const.ENoError)
        response = Mock()
        for callback in (client._auth_act, client._refresh_token_act):
            self.assertEqual(callback(response, None), const.ENoError)
        self.assertEqual(client._store_json.call_count, 2)

    def test_empty_credentials_fail_before_filesystem_or_auth(self):
        for key, secret in [('', 'test-secret'), ('test-key', ''), ('', '')]:
            with self.subTest(key=key, secret=secret):
                with patch.object(ByPy, 'migratesettings') as migrate:
                    with self.assertRaises(ValueError):
                        ByPy(apikey=key, secretkey=secret)
                    migrate.assert_not_called()
