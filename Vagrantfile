ENV['VAGRANT_DEFAULT_PROVIDER'] = 'libvirt'

Vagrant.configure("2") do |config|

  # config.vm.box = "ubuntu/trusty64"

  # config.vm.define :devstack do |devstack|
  #   devstack.vm.hostname = 'devstack'

  #   devstack.vm.network :private_network, ip: '192.168.76.2'

  #   devstack.vm.network :forwarded_port, guest: 80, host: 8080      # Horizon
  #   devstack.vm.network :forwarded_port, guest: 5000, host: 5000    # Keystone
  #   devstack.vm.network :forwarded_port, guest: 8774, host: 8774    # Nova

  #   # share the development directories with the vm
  #   devstack.vm.synced_folder "../", "/trove", owner: "vagrant", group: "vagrant"
  #   devstack.vm.synced_folder "../trove", "/opt/stack/trove",
  #     owner: "vagrant", group: "vagrant"
  #   devstack.vm.synced_folder "../horizon", "/opt/stack/horizon",
  #     owner: "vagrant", group: "vagrant"
  #   devstack.vm.synced_folder "../trove-tester", "/opt/stack/trove-tester",
  #     owner: "vagrant", group: "vagrant"
  #   devstack.vm.synced_folder "../python-troveclient", "/opt/stack/python-troveclient",
  #     owner: "vagrant", group: "vagrant"
  #   devstack.vm.synced_folder "../trove-integration", "/opt/stack/trove-integration",
  #     owner: "vagrant", group: "vagrant"

  #   devstack.vm.provider "virtualbox" do |vb|
  #     vb.customize ["modifyvm", :id, "--memory", 8192]
  #     vb.customize ["modifyvm", :id, "--cpus", 2]
  #     vb.customize ["modifyvm", :id, "--nicpromisc3", "allow-all"]
  #   end

  #   devstack.vm.provision :shell, :inline => <<-SCRIPT
  #     apt-get update
  #     apt-get -y install git curl wget build-essential python-mysqldb \
  #       python-dev libssl-dev python-pip git-core libxml2-dev libxslt-dev \
  #       python-pip libmysqlclient-dev screen emacs24-nox \
  #       libsasl2-dev tmux
  #     pip install virtualenv
  #     pip install tox==1.6.1
  #     pip install setuptools
  #     mkdir -p /opt/stack
  #     chown vagrant /opt/stack
  #   SCRIPT

  #   devstack.vm.provision :shell, :inline => <<-SCRIPT
  #     printf '\nexport USING_VAGRANT=true' >> /home/vagrant/.bashrc
  #   SCRIPT

  #   devstack.vm.provision "shell", path: "prep.sh"
  # end

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end

  config.vm.define :devstack do |machine|

    # It should be an Ubuntu 14.04 box
    machine.vm.box = "ubuntu/trusty64"

    # networking
    machine.vm.network "private_network", ip: '192.168.33.10'
    # machine.vm.network "public_network"
    machine.vm.network "forwarded_port", guest: 80, host: 8080

    # With so much RAM and CPUs
    machine.vm.provider :libvirt do |domain|
      domain.memory = 32768
      domain.cpus = 4
      domain.nested = true
    end

    # Finally, let's provision it by running a script. You can also run
    # puppet, chef, ansible, and others. Check the Vagrant website for
    # details.
    # machine.vm.provision :shell, path: "bootstrap.sh", args: "42", keep_color: true

    # share the development directories with the vm

    # machine.vm.synced_folder ".", "/vagrant", owner: "vagrant", group: "vagrant", type: "rsync"

    machine.vm.synced_folder "../trove", "/opt/stack/trove",
      owner: "vagrant", group: "vagrant", type: "rsync", rsync__exclude: [".tox/", "*.egg-info/", "*.log", "*.sqlite"]
    machine.vm.synced_folder "../trove-integration", "/opt/stack/trove-integration",
      owner: "vagrant", group: "vagrant", type: "rsync", rsync__exclude: [".tox/", "*.egg-info/", "*.log", "*.sqlite", "scripts/.cache/"]
    machine.vm.synced_folder "../python-troveclient", "/opt/stack/python-troveclient",
      owner: "vagrant", group: "vagrant", type: "rsync", rsync__exclude: [".tox/", "*.egg-info/", "*.log", "*.sqlite"]
    machine.vm.synced_folder "../trove-tester", "/opt/stack/trove-tester",
      owner: "vagrant", group: "vagrant", type: "rsync", rsync__exclude: [".tox/", "*.egg-info/", "*.log", "*.sqlite", "_tmp_package/"]

    machine.vm.synced_folder "../trove-dashboard", "/opt/stack/trove-dashboard",
      owner: "vagrant", group: "vagrant", type: "rsync", rsync__exclude: [".tox/", ".venv", "*.pyc", "*.egg-info/", "*.log", "*.sqlite"]

    # machine.vm.provision :shell, :inline => <<-SCRIPT
    #   apt-get update
    #   apt-get -y install git curl wget build-essential python-mysqldb \
    #     python-dev libssl-dev python-pip git-core libxml2-dev libxslt-dev \
    #     python-pip libmysqlclient-dev screen emacs24-nox \
    #     libsasl2-dev tmux
    #   pip install virtualenv
    #   pip install tox==1.6.1
    #   pip install setuptools
    #   mkdir -p /opt/stack
    #   chown vagrant /opt/stack
    # SCRIPT

    machine.vm.provision :shell, :inline => <<-SCRIPT
      printf '\nexport USING_VAGRANT=true' >> /home/vagrant/.bashrc
      printf '\nexport USE_LARGE_VOLUME=true' >> /home/vagrant/.bashrc
      printf '\nexport USE_KVM=true' >> /home/vagrant/.bashrc
    SCRIPT

    machine.vm.provision "shell", path: "prep.sh", args: "vagrant"

  end

end
