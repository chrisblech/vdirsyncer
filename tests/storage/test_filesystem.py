# -*- coding: utf-8 -*-

import os
import subprocess
import sys

import pytest

from vdirsyncer.exceptions import AlreadyExistingError
from vdirsyncer.storage.filesystem import FilesystemStorage
from vdirsyncer.utils.vobject import Item

from . import StorageTests


class TestFilesystemStorage(StorageTests):
    storage_class = FilesystemStorage

    @pytest.fixture(autouse=True)
    def setup(self, tmpdir):
        self.tmpdir = str(tmpdir)

    @pytest.fixture
    def get_storage_args(self):
        def inner(collection=None):
            path = self.tmpdir
            if collection is not None:
                os.makedirs(os.path.join(path, collection))
                path = os.path.join(path, collection)
            return {'path': path, 'fileext': '.txt', 'collection': collection}
        return inner

    def test_is_not_directory(self, tmpdir):
        with pytest.raises(IOError):
            f = tmpdir.join('hue')
            f.write('stub')
            self.storage_class(str(tmpdir) + '/hue', '.txt')

    def test_broken_data(self, tmpdir):
        s = self.storage_class(str(tmpdir), '.txt')

        class BrokenItem(object):
            raw = u'Ц, Ш, Л, ж, Д, З, Ю'.encode('utf-8')
            uid = 'jeezus'
            ident = uid
        with pytest.raises(TypeError):
            s.upload(BrokenItem)
        assert not tmpdir.listdir()

    def test_ident_with_slash(self, tmpdir):
        s = self.storage_class(str(tmpdir), '.txt')
        s.upload(Item(u'UID:a/b/c'))
        item_file, = tmpdir.listdir()
        assert str(item_file).endswith('a_b_c.txt')

    def test_too_long_uid(self, tmpdir):
        s = self.storage_class(str(tmpdir), '.txt')
        item = Item(u'UID:' + u'hue' * 600)
        href, etag = s.upload(item)
        assert item.uid not in href

    def test_post_hook_inactive(self, tmpdir, monkeypatch):

        def check_call_mock(*args, **kwargs):
            assert False

        monkeypatch.setattr(subprocess, 'call', check_call_mock)

        s = self.storage_class(str(tmpdir), '.txt', post_hook=None)
        s.upload(Item(u'UID:a/b/c'))

    def test_post_hook_active(self, tmpdir, monkeypatch):

        calls = []
        exe = 'foo'

        def check_call_mock(l, *args, **kwargs):
            calls.append(True)
            assert len(l) == 2
            assert l[0] == exe

        monkeypatch.setattr(subprocess, 'call', check_call_mock)

        s = self.storage_class(str(tmpdir), '.txt', post_hook=exe)
        s.upload(Item(u'UID:a/b/c'))
        assert calls
