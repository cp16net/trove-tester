#!/bin/bash

puppet apply --debug --verbose --modulepath=/home/ubuntu/system-config/modules:/etc/puppet/modules -e "class { openstack_project::single_use_slave: install_users => false, ssh_key => \"$( cat /home/ubuntu/.ssh/id_rsa.pub | awk '{print $2}' )\" }"
