from fabric.api import abort
from fabric.api import env
from fabric.api import lcd
from fabric.api import local
from fabric.api import run
from fabric.api import sudo
from fabric.api import task
from fabric.colors import green
from fabric.colors import cyan
from fabric.operations import prompt
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists
from fabric.contrib.console import confirm
from fabric.contrib.files import sed

from neutronclient.neutron import client as nclient
from novaclient import client
from novaclient.v2.shell import _poll_for_status


OS_VERSION = env.OS_VERSION
OS_USERNAME = env.OS_USERNAME
OS_PASSWORD = env.OS_PASSWORD
OS_TENANT_NAME = env.OS_TENANT_NAME
OS_TENANT_ID = env.OS_TENANT_ID
OS_AUTH_URL = env.OS_AUTH_URL
OS_REGION_NAME = env.OS_REGION_NAME
KEYPAIR_NAME = env.KEYPAIR_NAME

SYNC_EXCLUDES = ('*.vagrant', '*.tox', '*.log', '*.cache', '*.pyc', '*.venv')
SSH_CONFIG = '~/.ssh/config'
REMOTE_HOSTS_FILE = '/etc/hosts'

env.use_ssh_config = True


@task
def sync(project=None):
    """Sync the local code to the server"""
    sed(REMOTE_HOSTS_FILE,
        '^127.0.0.1 localhost$',
        '127.0.0.1 localhost %s' % env.host_string,
        use_sudo=True)
    if not exists('/opt/stack'):
        sudo('mkdir -p /opt/stack')
        whoami = run("whoami")
        sudo('chown %s -R /opt/stack' % whoami)
    if project:
        rsync_project(local_dir="../%s/" % project,
                      remote_dir="/opt/stack/%s" % project,
                      exclude=SYNC_EXCLUDES)
    else:
        rsync_project(local_dir="../",
                      remote_dir="/opt/stack",
                      exclude=SYNC_EXCLUDES)
    prep(run_once=True)


@task
def host():
    if not env.host_string:
        # get host list from .ssh/config file
        hosts = local('cat ~/.ssh/config | grep "Host "', capture=True)
        hosts = hosts.split('\n')
        hosts = [host.split(' ')[1] for host in hosts]
        for x, host in enumerate(hosts):
            print(green('%s\t%s' % (x, host)))
        selected_host = prompt("Choose a host:")
        env.hosts = [hosts[int(selected_host)]]
        print(cyan("Using host:" % env.hosts))


@task
def prep(run_once=None):
    test_file = "/home/ubuntu/.my.cnf"
    if run_once:
        if exists(test_file):
            print(cyan("Prep has already run."))
            return
    sudo('/opt/stack/trove-tester/prep.sh')


@task
def update():
    """Update the local code with the latest changes from github"""
    for d in ['trove', 'trove-integration', 'python-troveclient']:
        with lcd('../%s' % d):
            status = local('git status --short', capture=True)
            if status:
                print(status)
                abort("directory is not clean")
            local("git fetch origin")
            local("git pull --rebase origin master")


@task
def list():
    """List the servers on the cloud"""
    with client.Client(OS_VERSION,
                       OS_USERNAME,
                       OS_PASSWORD,
                       tenant_id=OS_TENANT_ID,
                       auth_url=OS_AUTH_URL,
                       region_name=OS_REGION_NAME) as cli:
        instances = cli.servers.list()
        for inst in instances:
            print(inst.name, inst.addresses)


@task
def boot(name=None):
    """Boot a new server"""
    with client.Client(OS_VERSION,
                       OS_USERNAME,
                       OS_PASSWORD,
                       tenant_id=OS_TENANT_ID,
                       auth_url=OS_AUTH_URL,
                       region_name=OS_REGION_NAME) as cli:
        flavor = _flavor_list(cli)
        image = _image_list(cli)
        network = _network_list()
        print(cyan('%s, %s, %s' % (flavor, image, network)))
        server_name = name or prompt("Choose a server name:")
        nics = [{'net-id': network['id']}]
        if not confirm("Do you wish to create the server?"):
            abort("Not building the server.")
        instance = cli.servers.create(
            name=server_name,
            flavor=flavor.id,
            image=image.id,
            key_name=KEYPAIR_NAME,
            nics=nics)
        _poll_for_status(cli.servers.get,
                         instance.id,
                         'building',
                         ['active'])
        # add floating ip after creating the server
        floating_ip = _floating_ip_list(cli)
        print(floating_ip)
        instance.add_floating_ip(floating_ip)


def _flavor_list(client):
    print('Flavors')
    flavors = client.flavors.list()
    output = "{id:<4s}{name:21s}{ram:6s}{vcpus}".format(
            id="ID",
            name="NAME",
            ram="RAM",
            vcpus="VCPUS",
            )
    print(green(output))
    for x, f in enumerate(flavors, 1):
        output = "{id:<4d}{name:16s}{ram:8d}{vcpus:4d}".format(
            id=x,
            name=f.name,
            ram=f.ram,
            vcpus=f.vcpus,
            )
        print(green(output))
    selected_flavor = prompt("Choose a flavor number:")
    return flavors[int(selected_flavor)-1]


def _image_list(client):
    print('Images')
    images = client.images.list()
    print(images[0].__dict__)
    sorted_images = sorted(images, key=lambda x: x.name)
    sorted_images = [image for image in sorted_images
                     if 'deprecated' not in image.name]
    for x, i in enumerate(sorted_images, 1):
        print(green('%s\t%s' % (x, i.name)))
    selected_image = prompt("Choose an image number:", default='40')
    return sorted_images[int(selected_image)-1]


def _network_list():
    print('Networks')
    neutron = nclient.Client('2.0',
                             username=OS_USERNAME,
                             password=OS_PASSWORD,
                             tenant_id=OS_TENANT_ID,
                             auth_url=OS_AUTH_URL,
                             region_name=OS_REGION_NAME)
    networks = neutron.list_networks().get('networks')
    for x, n in enumerate(networks, 1):
        print(green('%s\t%s' % (x, n['name'])))
    selected_network = prompt("Choose a network number:")
    return networks[int(selected_network)-1]


def _floating_ip_list(client):
    floating_ips = client.floating_ips.list()
    output = "{id:<4s}{ip:18s}{fixed_ip}".format(
            id="ID",
            ip="PUBLIC_IP",
            fixed_ip="FIXED_IP"
            )
    print(green(output))
    for x, i in enumerate(floating_ips, 1):
        output = "{id:<4d}{ip:18s}{fixed_ip:8s}".format(
            id=x,
            ip=i.ip,
            fixed_ip=i.fixed_ip,
            )
        print(green(output))
    selected_floating_ip = prompt("Choose a floating ip number:")
    return floating_ips[int(selected_floating_ip)-1]
