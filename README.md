# SSHConfigFS

`SSHConfigFS` is a FUSE filesystem to build SSH client config files on–the–fly.

If your `~/.ssh/config` is anything like mine, then it's pretty long (and only seems to grow).  Rather than having to continue managing one big file, I wrote this FUSE filesystem to instead build a config "file" dynamically from many smaller logical chunks.

## Requirements

Depends on the *fusepy* python package.  See `requirements.txt`.

I wrote this using Python 2.7.3 on OSX, with the [Fuse4X](http://fuse4x.github.com/) kernel extension. The *fusepy* package also supports Linux FUSE so it should work well on that platform, too.

## Explanation

To start, run the `sshconfigfs.py` script.  There are no arguments, yet, and it will run in the foreground.

The directory `~/.ssh/config.d/` is monitored for changes to its `mtime`.  Whenever one of the files inside `~/.ssh/config.d/` changes, it triggers re-generation of the combined config. 
For a chunk of config to be included in the final output, it must start with a number.  In `~/.ssh/config.d/` I keep several files:

    10_base
    15_tunnels
    20_workhosts
    30_personalhosts

These files are combined in the order they appear above, using shell–style globbing, into a single "file" contained within the FUSE mountpoint `~/.sshconfigfs/` (the combined file is called `config`).

You could create a symbolic link from `~/.ssh/config` to the generated `~/.sshconfigfs/config` file, so `ssh` can find it, or use the `-F` argument to `ssh` to point it directly at the generated file.

To give another example of use, I have a *crontab* entry periodically generating *ssh* `Host…` config chunks—using data from VPS provider's APIs—which are then written to files inside `~/.ssh/config.d/`.  This keeps my config up to date without my having to manually manage a large, somewhat dynamic, list of hosts.

## Run at startup

I use OSX.  To keep `SSHConfigFS` running, I use the included `.plist` file to tell OSX's `launchd` to run the `sshconfigfs.py` script to mount the filesystem.

    mkdir -p ~/Library/LaunchAgents

Edit the `com.markhellewell.SSHConfigFS.plist` file and change the path to the `sshconfigfs.py` script.  Then:

    cp com.markhellewell.SSHConfigFS.plist ~/Library/LaunchAgents/
    launchctl load -w ~/Library/LaunchAgents/com.markhellewell.SSHConfigFS.plist

This will keep the `SSHConfigFS` mounted, as your user, forever.

## TODO

* dæmonized mode support (at the moment will only run in the foreground)
* take arguments to configure `configd_dir` etc.
* pie shop?
