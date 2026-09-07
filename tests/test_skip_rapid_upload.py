"""Offline upload routing tests; never access a Baidu account."""
import contextlib
import io
import unittest
from unittest.mock import Mock, patch

from bypy import ByPy
from bypy import const
from bypy.bypy import getparser


class SkipRapidUploadTests(unittest.TestCase):
    def client(self, skip=False, only=False, rapid_result=const.ENoError):
        client = object.__new__(ByPy)
        client._skip_rapid_upload = skip
        client._rapiduploadonly = only
        client._slice_size = const.DefaultSliceSize
        client._shallinclude = Mock(return_value=True)
        client.pd = Mock()
        client.pv = Mock()
        client._rapidupload_file = Mock(return_value=rapid_result)
        client._upload_one_file = Mock(return_value=const.ENoError)
        client._upload_file_slices = Mock(return_value=const.ENoError)
        client._remove_local_on_success = Mock()
        return client

    def upload(self, client, size):
        with patch('bypy.bypy.getfilesize', return_value=size):
            return client._upload_file('local.zip', '/remote.zip', 'newcopy')

    def test_skip_routes_small_medium_and_large_files(self):
        for size, sliced in [(1, False), (const.MinRapidUploadFileSize + 1, False),
                             (const.DefaultSliceSize + 1, True)]:
            with self.subTest(size=size):
                client = self.client(skip=True)
                self.assertEqual(self.upload(client, size), const.ENoError)
                client._rapidupload_file.assert_not_called()
                used = client._upload_file_slices if sliced else client._upload_one_file
                unused = client._upload_one_file if sliced else client._upload_file_slices
                used.assert_called_once_with('local.zip', '/remote.zip', 'newcopy')
                unused.assert_not_called()
                client._remove_local_on_success.assert_called_once_with('local.zip')

    def test_default_still_uses_rapid_upload(self):
        client = self.client()
        self.assertEqual(self.upload(client, const.DefaultSliceSize + 1), const.ENoError)
        client._rapidupload_file.assert_called_once()
        client._upload_file_slices.assert_not_called()
        self.assertTrue(client._rapiduploaded)

    def test_failed_rapid_upload_still_falls_back(self):
        client = self.client(rapid_result=const.IEMD5NotFound)
        self.assertEqual(self.upload(client, const.DefaultSliceSize + 1), const.ENoError)
        client._upload_file_slices.assert_called_once()

    def test_rapid_upload_only_still_skips_misses(self):
        client = self.client(only=True, rapid_result=const.IEMD5NotFound)
        self.assertEqual(self.upload(client, const.DefaultSliceSize + 1), const.ESkipped)
        client._upload_file_slices.assert_not_called()
        client._remove_local_on_success.assert_not_called()

    def test_failed_normal_upload_does_not_remove_source(self):
        client = self.client(skip=True)
        client._upload_file_slices.return_value = const.ERequestFailed
        self.assertEqual(self.upload(client, const.DefaultSliceSize + 1), const.ERequestFailed)
        client._remove_local_on_success.assert_not_called()

    def test_cli_default_flag_and_conflict(self):
        parser = getparser()
        self.assertFalse(parser.parse_args(['upload']).skip_rapid_upload)
        self.assertTrue(parser.parse_args(['--skip-rapid-upload', 'syncup']).skip_rapid_upload)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            parser.parse_args(['--skip-rapid-upload', '--rapid-upload-only', 'upload'])
        self.assertEqual(error.exception.code, 2)

    def test_python_api_rejects_conflict_before_initialization(self):
        with patch.object(ByPy, 'migratesettings') as load_auth:
            with self.assertRaises(ValueError):
                ByPy(skip_rapid_upload=True, rapiduploadonly=True)
            load_auth.assert_not_called()


if __name__ == '__main__':
    unittest.main()
