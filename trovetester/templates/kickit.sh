sudo apt-get -y update
sudo apt-get -y install vim git
sudo rm -r /opt/
sudo mkdir /mnt/opt
sudo ln -s /mnt/opt /opt
sudo chmod -R 777 /mnt/opt
mkdir /opt/stack
{% for review in review_list -%}
cd /opt/stack
git clone https://github.com/openstack/{{ review.project }}.git
cd {{ review.project }}
{{ review.checkout_command }}
{% endfor -%}
cd ~
git clone https://github.com/openstack-dev/devstack.git
cd /opt/stack
if [ ! -d trove-integration ]; then
    git clone https://github.com/openstack/trove-integration.git
fi
cd trove-integration/scripts
./redstack install
./redstack kick-start mysql
./redstack int-tests
