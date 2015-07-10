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
        '127.0.0.1 localhost',
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
    rsync_project(local_dir="../",
                  remote_dir="/opt/stack",
                  exclude=SYNC_EXCLUDES)
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
        network = _network_list(cli)
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
    for x, f in enumerate(flavors):
        print(green('%s\t%s\t\t%s' % (x, f.name, f.ram)))
    selected_flavor = prompt("Choose a flavor number:")
    return flavors[int(selected_flavor)]


def _image_list(client):
    print('Images')
    images = client.images.list()
    for x, i in enumerate(images):
        if 'deprecated' in i.name:
            continue
        else:
            print(green('%s\t%s' % (x, i.name)))
    selected_image = prompt("Choose an image number:")
    return images[int(selected_image)]


def _network_list(client):
    print('Networks')
    neutron = nclient.Client('2.0',
                             username=OS_USERNAME,
                             password=OS_PASSWORD,
                             tenant_id=OS_TENANT_ID,
                             auth_url=OS_AUTH_URL,
                             region_name=OS_REGION_NAME)
    networks = neutron.list_networks().get('networks')
    for x, n in enumerate(networks):
        print(green('%s\t%s' % (x, n['name'])))
    selected_network = prompt("Choose a network number:")
    return networks[int(selected_network)]

def _floating_ip_list(client):
    floating_ips = client.floating_ips.list()
    for x, i in enumerate(floating_ips):
        print(green('%s\t%s' % (x, i)))
    selected_floating_ip = prompt("Choose a floating ip number:")
    return floating_ips[int(selected_floating_ip)]
