
import os
import shutil
import tarfile
import hashlib
from setuptools import Command
from glob import glob

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

from .msg import fatal, debug, info, warn

pjoin = os.path.join

# https://github.com/zeromq/zyre/releases/download/v3.0.2/zyre-3.0.2.tar.gz
bundled_version = (0, 0, 4)
vs = '%i.%i.%i' % bundled_version
libzyre = "zyre-%s.tar.gz" % vs
libzyre_url = "https://github.com/zeromq/zyre/releases/download/v{vs}/{libzyre}".format(
    major=bundled_version[0],
    minor=bundled_version[1],
    vs=vs,
    libzyre=libzyre,
)
libzyre_checksum = "sha256:8bca39ab69375fa4e981daf87b3feae85384d5b40cef6adbe9d5eb063357699a"

commit = 'cdbaab7e67c8ec2c896ae1c13607f36194f2a196'
libzyre_url = 'https://github.com/zeromq/zyre/archive/{}.tar.gz'.format(commit)
libzyre_checksum = "sha256:a5e1c0bbbf8c1c827923c5515900913e641f861f4af9236d82591c63b471b253"

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def untgz(archive):
    return archive.replace('.tar.gz', '')


def localpath(*args):
    """construct an absolute path from a list relative to the root pyzmq directory"""
    plist = [ROOT] + list(args)
    return os.path.abspath(pjoin(*plist))


def checksum_file(scheme, path):
    """Return the checksum (hex digest) of a file"""
    h = getattr(hashlib, scheme)()

    with open(path, 'rb') as f:
        chunk = f.read(65535)
        while chunk:
            h.update(chunk)
            chunk = f.read(65535)
    return h.hexdigest()


def fetch_archive(savedir, url, fname, checksum, force=False):
    """download an archive to a specific location"""
    dest = pjoin(savedir, fname)
    scheme, digest_ref = checksum.split(':')

    if os.path.exists(dest) and not force:
        info("already have %s" % dest)
        digest = checksum_file(scheme, fname)
        if digest == digest_ref:
            return dest
        else:
            warn("but checksum %s != %s, redownloading." % (digest, digest_ref))
            os.remove(fname)

    info("fetching %s into %s" % (url, savedir))
    if not os.path.exists(savedir):
        os.makedirs(savedir)
    req = urlopen(url)
    with open(dest, 'wb') as f:
        f.write(req.read())
    digest = checksum_file(scheme, dest)
    if digest != digest_ref:
        fatal("%s %s mismatch:\nExpected: %s\nActual  : %s" % (
            dest, scheme, digest_ref, digest))
    return dest


def fetch_libzyre(savedir):
    dest = pjoin(savedir, 'zyre')
    if os.path.exists(dest):
        info("already have %s" % dest)
        return
    path = fetch_archive(savedir, libzyre_url, fname=libzyre, checksum=libzyre_checksum)
    tf = tarfile.open(path)
    with_version = pjoin(savedir, tf.firstmember.path)
    tf.extractall(savedir)
    tf.close()
    # remove version suffix:
    shutil.move(with_version, dest)


class FetchCommand(Command):

    description = "Fetch libzyre sources into bundled/zyre"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # fetch sources for libzmq extension:
        bundledir = "bundled"
        if os.path.exists(bundledir):
            info("Scrubbing directory: %s" % bundledir)
            shutil.rmtree(bundledir)
        if not os.path.exists(bundledir):
            os.makedirs(bundledir)
        fetch_libzyre(bundledir)
        for tarball in glob(pjoin(bundledir, '*.tar.gz')):
            os.remove(tarball)
