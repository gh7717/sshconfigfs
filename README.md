# A FUSE filesystem to dynamically build SSH config

If your `~/.ssh/config` is anything like mine, then it's pretty long (and only seems to grow).  Rather than having to continue managing one big file, I wrote this FUSE filesystem to instead build a config "file" dynamically from many smaller logical chunks.

## Requirements

See `requirements.txt`.  Currently depends on *fusepy* python package.

I wrote this on OSX, using the [Fuse4X](http://fuse4x.github.com/) kernel module. The *fusepy* package also supports FUSE on Linux so I don't see why it wouldn't work perfectly well on that platform.

## Example

For a chunk of config to be included in the final config, it must start with a number.  In `~/.ssh/config.d/` I keep several files:

    10_base
    15_tunnels
    20_workhosts
    30_personalhosts

`~/.ssh/config.d/` is monitored for changes to its `mtime`.  Whenever one of the files inside `~/.ssh/config.d/` changes, it triggers re-generation of the combined config.  These files are combined in the order they appear in above, using shell–style globbing, into a single "file" contained within the FUSE mountpoint `~/.sshconfigfs/` (the combined file is called `config`).

You should create a symbolic link from `~/.ssh/config` to the generated `~/.sshconfigfs/config` file, so `ssh` can find it.

To give another example of use, I have a *crontab* entry periodically generating *ssh* `Host…` config chunks—using data from VPS provider's APIs—which are then written to files inside `~/.ssh/config.d/`.  This keeps my config up to date without my having to manually manage a large, somewhat dynamic, list of hosts.

## TODO

* logging
* dæmonized mode support (at the moment will only run in the foreground)
* take arguments to configure `configd_dir` etc.
* `.plist` for Mac OS X's `launchd`
