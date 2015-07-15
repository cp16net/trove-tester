trove-tester
============

These are some scripts that help make development a bit easier with devstack
and Trove.

There is a vagrant file that i have not had much luck with in the last month but it
worked a while back. (needs some work)


Requirements
------------

    sudo pip install virtualenvwrapper

Add this to your ~/.bashrc or ~/.zshrc file.

    export WORKON_HOME=$HOME/.virtualenvs
    export PROJECT_HOME=$HOME/Devel
    export VIRTUALENVWRAPPER_SCRIPT=/usr/local/bin/virtualenvwrapper.sh
    source /usr/local/bin/virtualenvwrapper_lazy.sh

Copy the .fabricrc file to your home directory and edit the file with your
OpenStack credentials.

    cp fabricrc.example ~/.fabricrc
    emacs ~/.fabricrc

Fabric
------

Create a new virtualenv and install the dependencies (ALWAYS create new
python virutalenvs when working on a project)

    mkvirtualenv test
    pip install fabric
    fab -l

After you have the virtualenv and need to use it later do this.

    workon test
    fab -l
    fab -d boot


Setup
-----

In your OpenStack project make sure there are a few things setup prior to
running this.

- Add your keypair to the OpenStack deployment with a name that matches
the .fabricrc KEYPAIR_NAME.
- Create a devstack network that is 10.2.0.0/24
- Create an Interface on your router for 10.2.0.1
- Create some floating ips that are not attached to an instance.
- Add entries to your `~/.ssh/config` file of the names you want to use for
your floating ips you created


Examples
--------

List the all the servers and network ips attached

    fab list

Boot a new server as a choose your own adventure.

    fab boot

Syncronize the all the projects in `../` local directory to `/opt/stack`
remote directory. Also setup a few helper commands once you ssh into your
remote system.

    fab host sync

The command `host` will allow you to choose the host that you want to run
the following commands on. The `host` command reads the list of hosts
in your `~/.ssh/config` file. You can still pass in the host like below.

    fab -H myhost sync

ssh into your remote system after running the `fab sync` cmd and your should
have a few convience commands you are run.

- `redstack` - allows you to run the redstack cmd from any directory.
- `fix-iptables.sh` - allows the guest instances to talk out to the interwebs.


TODO
----

- work on Vagrantfile setup
- figure out a clean way of updating the .ssh/config without ruining
existing setup
