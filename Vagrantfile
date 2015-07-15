Vagrant.configure("2") do |config|

  config.vm.box = "ubuntu/trusty64"


  config.vm.define :devstack do |devstack|
    devstack.vm.hostname = 'devstack'

    devstack.vm.network :private_network, ip: '192.168.76.2'

    devstack.vm.network :forwarded_port, guest: 80, host: 8080      # Horizon
    devstack.vm.network :forwarded_port, guest: 5000, host: 5000    # Keystone
    devstack.vm.network :forwarded_port, guest: 8774, host: 8774    # Nova

    # share the development directories with the vm
    devstack.vm.synced_folder "../", "/trove", owner: "vagrant", group: "vagrant"
    devstack.vm.synced_folder "../trove", "/opt/stack/trove",
      owner: "vagrant", group: "vagrant"
    devstack.vm.synced_folder "../python-troveclient", "/opt/stack/python-troveclient",
      owner: "vagrant", group: "vagrant"
    devstack.vm.synced_folder "../trove-integration", "/opt/stack/trove-integration",
      owner: "vagrant", group: "vagrant"

    devstack.vm.provider "virtualbox" do |vb|
      vb.customize ["modifyvm", :id, "--memory", 8192]
      vb.customize ["modifyvm", :id, "--cpus", 2]
      vb.customize ["modifyvm", :id, "--nicpromisc3", "allow-all"]
    end

    devstack.vm.provision :shell, :inline => <<-SCRIPT
      apt-get update
      apt-get -y install git curl wget build-essential python-mysqldb \
        python-dev libssl-dev python-pip git-core libxml2-dev libxslt-dev \
        python-pip libmysqlclient-dev screen emacs24-nox \
        libsasl2-dev
      pip install virtualenv
      pip install tox==1.6.1
      pip install setuptools
      mkdir -p /opt/stack
      chown vagrant /opt/stack
    SCRIPT

    devstack.vm.provision :shell, :inline => <<-SCRIPT
      printf '\nexport USING_VAGRANT=true' >> /home/vagrant/.bashrc
    SCRIPT

    devstack.vm.provision "shell", path: "prep.sh"
  end
end
