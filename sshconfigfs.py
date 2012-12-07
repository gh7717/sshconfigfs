#!/usr/bin/env python
# FUSE filesystem to build SSH config file dynamically.
# Mark Hellewell <mark.hellewell@gmail.com>
import glob
import logging
import os
from stat import S_IFDIR, S_IFREG
#from sys import argv, exit
import threading
from time import sleep, time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

# TODO is there a "file" type object belonging to FUSE?  Would be
# better to extend that.

logger = logging.getLogger()
logger.setLevel(logging.INFO)

global configLock
global configDict
configLock = threading.Lock()
configDict = dict(config='', config_length=0)


class SSHConfigFS(LoggingMixIn, Operations):
    """Builds ssh's config file dynamically.
    """

    def __init__(self, ssh_dir, configd_dir):
        self.now = time()
        self.ssh_dir = ssh_dir
        self.configd_dir = configd_dir
        self.generate_config()

    def init(self, arg):
        # start the thread which polls configd_dir for changes to
        # contained files
        t = threading.Thread(target=self.dir_poller)
        t.start()

    def getattr(self, path, fh=None):
        try:
            # TODO the nlink value needs to be calculated based on
            # size of generated content, or an error is generated
            # saying too much data was read!
            # TODO use 'defaultdict' to avoid all the st_ repitition?
            fattr = {
                '/': dict(st_mode=(S_IFDIR | 0550),
                          st_uid=os.getuid(), # or user requested
                          st_gid=os.getgid(),
                          st_nlink=2,
                          st_ctime=self.now,
                          st_mtime=self.now,
                          st_atime=self.now),
                '/config': dict(st_mode=(S_IFREG | 0440),
                                st_uid=os.getuid(), # or user requested
                                st_gid=os.getgid(),
                                st_size=configDict['config_length'],
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
            return configDict['config']

    def readdir(self, path, fh):
        return ['.', '..', 'config',]

    def dir_poller(self):
        """Polls the configd_dir for changes, rebuilding the config
        when required.

        This is started as a thread from within the init() (not
        __init__) method."""
        orig_mod_timestamp = os.stat(self.configd_dir).st_mtime
        while True:
            sleep(0.5)
            now_mod_timestamp = os.stat(self.configd_dir).st_mtime
            if now_mod_timestamp != orig_mod_timestamp:
                self.generate_config()
                orig_mod_timestamp = now_mod_timestamp

    def generate_config(self):
        configLock.acquire()
        configDict['config'] = ''
        configDict['config_length'] = 0
        for conf_file in glob.iglob("{}/[0-9]*".format(self.configd_dir)):
            try:
                configDict['config'] += file(conf_file, 'r').read()
                configDict['config_length'] = len(configDict['config'])
                print "{} was included".format(conf_file)
            except IOError:
                print "IOError while tring to read {}: skipping!".format(conf_file)
                continue
        configLock.release()

    # def destroy(self, path):
    #     pass


if __name__ == '__main__':
    # TODO should take arguments for: user, config.d location, and?

    # TODO maybe better to default to using mountpoint of
    # ~/.sshconfigfs ?
    ssh_dir = os.path.join(os.path.expanduser('~'), '.ssh')

    # directory containing ssh config chunks
    configd_dir = os.path.join(ssh_dir, 'config.d')
    if not os.path.exists(configd_dir):
        os.mkdir(configd_dir)

    # where our filesystem will be mounted
    mountpoint = os.path.join(ssh_dir, '.sshconfigfs')
    if not os.path.exists(mountpoint):
        os.mkdir(mountpoint)

    fuse = FUSE(SSHConfigFS(ssh_dir, configd_dir), mountpoint, foreground=True)
