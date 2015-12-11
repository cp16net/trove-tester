#!/bin/bash

if [[ "a$@" == "a" ]]; then
    MY_USER=ubuntu
else
    MY_USER=$@
fi

echo "the install user is $MY_USER"

function add_redstack() {
	echo Creating redstack command
	REDSTACK="/usr/local/bin/redstack"
	if [ ! -e "$REDSTACK" ]; then
		echo "#!/bin/bash" > $REDSTACK
		echo "pushd /opt/stack/trove-integration/scripts" >> $REDSTACK
		echo "./redstack \$@" >> $REDSTACK
		echo "popd" >> $REDSTACK
		chmod +x $REDSTACK
	fi
}

function add_mycnf() {
    echo Adding .my.cnf file for easy DB access
    MYCNF="/home/$MY_USER/.my.cnf"
    if [ ! -e $MYCNF ]; then
        # Set SERVICE_HOST to not require extra functions
        SERVICE_HOST=localhost
        source /opt/stack/trove-integration/scripts/functions
        source /opt/stack/trove-integration/scripts/redstack.rc
        cat <<EOF >$MYCNF
[client]
user=root
password=$MYSQL_PASSWORD
EOF
        chown $MY_USER $MYCNF
    fi
}

function install_dependencies() {
    printf "deb http://archive.ubuntu.com/ubuntu trusty-backports main restricted universe multiverse\n" > /etc/apt/sources.list.d/backports.list
    apt-get update
    apt-get -y install git curl wget build-essential python-mysqldb libpq-dev \
        python-dev libssl-dev python-pip git-core libxml2-dev libxslt-dev \
        python-pip libmysqlclient-dev screen emacs24-nox \
        libsasl2-dev tmux ruby
    pip install virtualenv
    pip install tox==1.6.1
    pip install setuptools
    cp /opt/stack/trove-tester/files/.gitconfig /home/$MY_USER/.gitconfig
    chown $MY_USER:$MY_USER /home/$MY_USER/.gitconfig
    cp /opt/stack/trove-tester/files/.ssh_config /home/$MY_USER/.ssh/config
    chown $MY_USER:$MY_USER /home/$MY_USER/.ssh/config
    gem install tmuxinator
    wget https://raw.githubusercontent.com/tmuxinator/tmuxinator/master/completion/tmuxinator.bash -O /home/$MY_USER/.tmuxinator.bash
    chown $MY_USER:$MY_USER /home/$MY_USER/.tmuxinator.bash

    printf "\nsource ~/.tmuxinator.bash \nsource ~/devstack/openrc alt_demo alt_demo\n" >> /home/$MY_USER/.bashrc

    chown $MY_USER:$MY_USER /home/$MY_USER/.bashrc
    mkdir -p /home/$MY_USER/.tmuxinator/
    cp /opt/stack/trove-tester/files/devstack-dev.yml /home/$MY_USER/.tmuxinator/
    chown $MY_USER:$MY_USER -R /home/$MY_USER/.tmuxinator/

}

function add_ssh_keys() {
    FILES=/opt/stack/trove-tester/files/sshkeys/*
    for f in $FILES
    do
      echo "Processing $f file..."
      # take action on each file. $f store current file name
      cat $f >> /home/$MY_USER/.ssh/authorized_keys
    done
    chown $MY_USER:$MY_USER /home/$MY_USER/.ssh/authorized_keys
}

# add_fix_iptables
add_redstack
add_mycnf
install_dependencies
add_ssh_keys

# this never works right... i think because it times out or something.
# sudo su - $MY_USER -c "redstack install && redstack kick-start mysql"

pushd /opt/stack/trove
TROVE_BRANCH=$(git rev-parse --abbrev-ref HEAD)
popd

echo "DO THIS STUFF"
echo "TROVE_BRANCH=${TROVE_BRANCH} redstack install && redstack kick-start mysql"
echo ""
echo "love me some tmux."
echo ""
echo "mux start devstack-dev"
