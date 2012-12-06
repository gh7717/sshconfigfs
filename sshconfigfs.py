#!/usr/bin/env python

#from collections import defaultdict
import glob
import logging
import os
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SSHConfigFS(LoggingMixIn, Operations):
    """Builds ssh's config file dynamically.
    """

    def __init__(self, ssh_dir):
        self.now = time()
        self.ssh_dir = ssh_dir
        self.configd_dir = os.path.join(self.ssh_dir, 'config.d')
        if not os.path.exists(self.configd_dir):
            os.mkdir(self.configd_dir)

        # generate config
        self.config = ''
        for conf_chunk in glob.glob("{}/[0-9]*".format(self.configd_dir)):
            print "{} is being included".format(conf_chunk)
            self.config += file(conf_chunk, 'r').read()
        self.config_size = len(self.config)
        # TODO I'd like to "watch" the contents of the
        # self.configd_dir for changes to files, so the config can be
        # rebuilt.

    def getattr(self, path, fh=None):
        try:
            # TODO the nlink value needs to be calculated based on
            # size of generated content, or an error is generated
            # saying too much data was read!
            fattr = {
                '/': dict(st_mode=(S_IFDIR | 0550),
                          st_uid=os.getuid(),
                          st_gid=os.getgid(),
                          st_nlink=2,
                          st_ctime=self.now,
                          st_mtime=self.now,
                          st_atime=self.now),
                '/config': dict(st_mode=(S_IFREG | 0440),
                                st_uid=os.getuid(),
                                st_gid=os.getgid(),
                                st_size=self.config_size,
                                st_nlink=2,
                                st_ctime=self.now,
                                st_mtime=self.now,
                                st_atime=self.now),
                }[path]
            return fattr
        except KeyError:
            return dict()

    def read(self, path, size, offset, fh):
        if path == '/config':
            return self.config

    def readdir(self, path, fh):
        return ['.', '..', 'config',]

    # def destroy(self, path):
    #     pass


if __name__ == '__main__':
    ssh_dir = os.path.join(os.path.expanduser('~'), '.ssh')
    mountpoint = os.path.join(ssh_dir, '.sshconfigfs')
    if not os.path.exists(mountpoint):
        os.mkdir(mountpoint)
    fuse = FUSE(SSHConfigFS(ssh_dir), mountpoint, foreground=True)
