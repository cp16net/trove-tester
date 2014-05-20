Vagrant.configure("2") do |config|
  config.vm.define :test_vm do |test_vm|
    test_vm.vm.box = "precise64"
    # test_vm.vm.network :private_network, :ip => '10.20.30.40'
    # config.vm.network :forwarded_port, guest: 80, host: 8080
  end

  config.vm.provision "shell", path: "outputkickit.sh"

  config.vm.provider :libvirt do |libvirt|
    libvirt.memory = 2048
    libvirt.cpus = 2
    #libvirt.driver = "qemu"
    #libvirt.host = "localhost"
    #libvirt.connect_via_ssh = true
    #libvirt.username = "root"
    #libvirt.storage_pool_name = "test"
  end
end