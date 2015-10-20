#!/bin/bash


# SETUP THE ENVIRONEMNT FOR JENKINS GATE
export REPO_URL=https://review.openstack.org/p
export ZUUL_URL=/home/jenkins/workspace-cache
export ZUUL_REF=HEAD
export WORKSPACE=/home/jenkins/workspace/testing
rm -rf $ZUUL_URL/*
rm -rf $WORKSPACE
mkdir -p $WORKSPACE

# SPECIFY THE PROJECT AND BRANCH TO TEST
export ZUUL_PROJECT=openstack/trove
export ZUUL_BRANCH=master
export DATASTORE_TEST=mysql

# GET COPY OF PROJECT WE ARE TESTING
git clone $REPO_URL/$ZUUL_PROJECT $ZUUL_URL/$ZUUL_PROJECT \
&& cd $ZUUL_URL/$ZUUL_PROJECT \
&& git checkout remotes/origin/$ZUUL_BRANCH

# GET DEVSTACK GATE PROJECT
cd $WORKSPACE \
&& git clone $REPO_URL/openstack-infra/devstack-gate

# RUN THE GATE JOB STUFF
export PYTHONUNBUFFERED=true
export DEVSTACK_GATE_TIMEOUT=140
export DEVSTACK_LOCAL_CONFIG="enable_plugin trove git://git.openstack.org/openstack/trove"
export DEVSTACK_PROJECT_FROM_GIT=python-troveclient
export ENABLED_SERVICES=tempest,s-proxy,s-object,s-container,s-account,trove,tr-api,tr-tmgr,tr-cond
export PROJECTS="openstack/trove-integration openstack/diskimage-builder openstack/tripleo-image-elements $PROJECTS"
function post_test_hook {
  export BRIDGE_IP=10.1.0.1
  export DEST=$BASE/new
  export PATH_DEVSTACK_SRC=$DEST/devstack
  cd /opt/stack/new/trove-integration/scripts
  ./redstack dsvm-gate-tests $DATASTORE_TEST
}
export -f post_test_hook
export BRANCH_OVERRIDE={branch-override}
if [ "$BRANCH_OVERRIDE" != "default" ] ; then
  export OVERRIDE_ZUUL_BRANCH=$BRANCH_OVERRIDE
fi
pwd

    cp devstack-gate/devstack-vm-gate-wrap.sh ./safe-devstack-vm-gate-wrap.sh
echo "now run this command: ./safe-devstack-vm-gate-wrap.sh"
