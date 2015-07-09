#!/bin/bash


function add_fix_iptables() {
	echo Creating fix-iptables.sh
	FIXSH="/usr/local/bin/fix-iptables.sh"
	if [ ! -e "$FIXSH" ]; then
		echo "#!/bin/bash" > $FIXSH
		echo "sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE" >> $FIXSH
		chmod +x $FIXSH
	fi
}

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

add_fix_iptables
add_redstack
add_mycnf

# TODO(cp16net) maybe i should run this inline as the vagrant/ubuntu user
echo "redstack install && redstack kick-start mysql && fix-iptables.sh"
