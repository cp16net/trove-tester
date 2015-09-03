from os.path import expanduser

from fabric.api import abort
from fabric.api import env
from fabric.api import local
from fabric.api import run
from fabric.api import sudo
from fabric.api import task
from fabric.colors import green
from fabric.colors import cyan
from fabric.colors import yellow
from fabric.operations import prompt
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists
from fabric.contrib.console import confirm
from fabric.contrib.files import sed

from neutronclient.neutron import client as nclient
from novaclient import client
from novaclient.v2.shell import _poll_for_status

from paramiko.config import SSHConfig

try:
    OS_VERSION = env.OS_VERSION
    OS_USERNAME = env.OS_USERNAME
    OS_PASSWORD = env.OS_PASSWORD
    OS_TENANT_NAME = env.OS_TENANT_NAME
    OS_TENANT_ID = env.OS_TENANT_ID
    OS_AUTH_URL = env.OS_AUTH_URL
    OS_REGION_NAME = env.OS_REGION_NAME
    KEYPAIR_NAME = env.KEYPAIR_NAME
except AttributeError:
    abort("Need to setup ~/.fabricrc file!")

SYNC_EXCLUDES = ('*.vagrant', '*.tox', '*.log', '*.cache', '*.pyc',
                 '*.venv', '*.sqlite*', 'cover/', '.testrepository',
                 '*.egg*')
SSH_CONFIG = '~/.ssh/config'
REMOTE_HOSTS_FILE = '/etc/hosts'

env.use_ssh_config = True


@task
def host():
    """Interactively choose a host to perform action on."""
    if not env.host_string:
        # get host list from .ssh/config file
        hosts = local('cat ~/.ssh/config | grep "Host "', capture=True)
        hosts = hosts.split('\n')
        hosts = [host.split(' ')[1] for host in hosts if not host.startswith('#')]
        for x, host in enumerate(hosts):
            print(green('%s\t%s' % (x, host)))
        selected_host = prompt("Choose a host:")
        env.hosts = [hosts[int(selected_host)]]
        print(cyan("Using host:" % env.hosts))


def prep(run_once=None):
    """Preps the host by setting up """
    test_file = "/home/ubuntu/.my.cnf"
    if run_once:
        if exists(test_file):
            print(cyan("Prep has already run."))
            return
    sudo('/opt/stack/trove-tester/prep.sh', timeout=2400)


@task
def sync(project=None):
    """Sync the local code to the server and prep if needed."""
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
        server_name = name or prompt("Choose a server name:")
        nics = [{'net-id': network['id']}]
        print("%s%s" % (cyan('Name: '),
              green('%s' % server_name)))
        print("%s%s" % (cyan('Flavor: '),
              green('%s' % flavor.name)))
        print("%s%s" % (cyan('Image: '), green('%s' % image.name)))
        print("%s%s" % (cyan('Network: '), green('%s' % network['name'])))
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
        floating_ip = _floating_ip_list(cli, server_name)
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
    default_flavor_name = None
    default_flavor_number = None
    for x, f in enumerate(flavors, 1):
        output = "{id:<4d}{name:16s}{ram:8d}{vcpus:4d}".format(
            id=x,
            name=f.name,
            ram=f.ram,
            vcpus=f.vcpus,
            )
        if 'standard.2xlarge' in f.name:
            default_flavor_name = f.name
            default_flavor_number = str(x)
            print(yellow(output))
        else:
            print(green(output))
    selected_flavor = prompt(
        "Choose a flavor number: (%s)" % yellow(default_flavor_name),
        default=default_flavor_number)
    return flavors[int(selected_flavor)-1]


def _image_list(client):
    print('Images')
    images = client.images.list()
    sorted_images = sorted(images, key=lambda x: x.name)
    sorted_images = [image for image in sorted_images
                     if 'deprecated' not in image.name]
    default_image_number = None
    default_image_name = None
    for x, i in enumerate(sorted_images, 1):
        if "Ubuntu Server 14.04.1 LTS " in i.name:
            default_image_number = str(x)
            default_image_name = i.name
            print(yellow('%s\t%s' % (x, i.name)))
        else:
            print(green('%s\t%s' % (x, i.name)))
    selected_image = prompt(
        "Choose an image number: (%s)" % yellow(default_image_name),
        default=default_image_number)
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
    default_network_name = None
    default_network_number = None
    for x, n in enumerate(networks, 1):
        if 'devstack' in n['name']:
            default_network_name = n['name']
            default_network_number = str(x)
            print(yellow('%s\t%s' % (x, n['name'])))
        else:
            print(green('%s\t%s' % (x, n['name'])))
    selected_network = prompt(
        "Choose a network number: (%s)" % yellow(default_network_name),
        default=default_network_number)
    return networks[int(selected_network)-1]


def _lookup_hostname_ip_in_ssh_config(hostname=None):
    config_file = file(expanduser('~/.ssh/config'))
    config = SSHConfig()
    config.parse(config_file)
    return config.lookup(hostname)['hostname']


def _lookup_ip_hostname(ip_address=None):
    config_file = file(expanduser('~/.ssh/config'))
    config = SSHConfig()
    config.parse(config_file)
    for host in config.get_hostnames():
        host_info = config.lookup(host)
        if host_info['hostname'] == ip_address:
            return host


def _floating_ip_list(client, server_name):
    floating_ips = client.floating_ips.list()
    suggested_ip = _lookup_hostname_ip_in_ssh_config(server_name)
    output = "{id:<4s}{ip:18s}{fixed_ip:16s}{ssh_config}".format(
            id="ID",
            ip="PUBLIC_IP",
            fixed_ip="FIXED_IP",
            ssh_config="SSH_CONFIG"
            )
    print(green(output))
    default_ip = None
    default_ip_number = None
    for x, i in enumerate(floating_ips, 1):
        output = "{id:<4d}{ip:18s}{fixed_ip:16s}{ssh_config}".format(
            id=x,
            ip=i.ip,
            fixed_ip=i.fixed_ip,
            ssh_config=_lookup_ip_hostname(i.ip)
            )
        if suggested_ip in i.ip:
            default_ip = i.ip
            default_ip_number = str(x)
            print(yellow(output))
        else:
            print(green(output))
    selected_floating_ip = prompt(
        "Choose a floating ip number: (%s)" % yellow(default_ip),
        default=default_ip_number)
    return floating_ips[int(selected_floating_ip)-1]


# @task
# def update():
#     """Update the local code with the latest changes from github"""
#     for d in ['trove', 'trove-integration', 'python-troveclient']:
#         with lcd('../%s' % d):
#             status = local('git status --short', capture=True)
#             if status:
#                 print(status)
#                 abort("directory is not clean")
#             local("git fetch origin")
#             local("git pull --rebase origin master")


# @task
# def list():
#     """List the servers on the cloud"""
#     with client.Client(OS_VERSION,
#                        OS_USERNAME,
#                        OS_PASSWORD,
#                        tenant_id=OS_TENANT_ID,
#                        auth_url=OS_AUTH_URL,
#                        region_name=OS_REGION_NAME) as cli:
#         instances = cli.servers.list()
#         for inst in instances:
#             print(inst.name, inst.addresses)
