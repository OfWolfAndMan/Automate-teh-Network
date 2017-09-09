#!/bin/bash

pip2 install -r ansible-requirements.txt
mkdir ~/Documents/Ansible
cd ~/Documents/Ansible
git clone https://github.com/networktocode/ntc-ansible
cd ntc-ansible
sudo python setup.py install
