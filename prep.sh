#!/bin/bash

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
    MYCNF="/home/ubuntu/.my.cnf"
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
        chown ubuntu $MYCNF
    fi
}

function install_dependencies() {
    apt-get update
    apt-get -y install git curl wget build-essential python-mysqldb \
        python-dev libssl-dev python-pip git-core libxml2-dev libxslt-dev \
        python-pip libmysqlclient-dev screen emacs24-nox \
        libsasl2-dev tmux
    pip install virtualenv
    pip install tox==1.6.1
    pip install setuptools
    cp /opt/stack/trove-tester/files/.gitconfig /home/ubuntu/.gitconfig
    chown ubuntu:ubuntu /home/ubuntu/.gitconfig
}

add_fix_iptables
add_redstack
add_mycnf
install_dependencies

sudo su - ubuntu -c "redstack install && redstack kick-start mysql"
