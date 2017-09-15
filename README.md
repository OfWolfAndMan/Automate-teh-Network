# Ansible Playbooks (Linux and Network Vendors)
## Version 1.0

An array of Ansible playbooks in the making for the benefit of automating all the things (Or those that should be).

Built in python 2.7, although will be migrated to python 3.6 soon due to nearing EOS state of 2.7.

**Tree Structure**
.
├── Development
│   ├── Inventory
│   │   ├── Inventory.csv
│   │   ├── SW4_inventory.txt
│   │   └── inventory_switches.textfsm
│   ├── L2int.j2
│   ├── change_hostname.yaml
│   ├── configtemplatingjinja.py
│   ├── iosparsefsm.py
│   ├── jinja-snippets.j2
│   ├── output.txt
│   ├── playbook-snippets.yml
│   ├── snippets.txt
├── Playbooks
│   ├── Linux
│   │   ├── PostGRE-Tables.yml
│   │   ├── ansible.cfg
│   │   ├── files
│   │   │   └── NetworkTables.sql
│   │   ├── group_vars
│   │   │   └── rpi.yml
│   │   ├── host_vars
│   │   ├── hosts
│   │   ├── implement_quagga.yml
│   │   ├── roles
│   │   │   └── nginx
│   │   │       ├── files
│   │   │       │   ├── generatetls.sh
│   │   │       │   ├── nginx.conf
│   │   │       │   ├── nginx.crt
│   │   │       │   └── nginx.key
│   │   │       └── templates
│   │   │           ├── index.html.j2
│   │   │           └── nginx.conf.j2
│   │   ├── update_packages.yml
│   │   ├── web-notls.yml
│   │   └── web-tls.yml
│   └── Network_Vendors
│       ├── CSRinterfaces.sql
│       ├── L2switches.yml
│       ├── ansible.cfg
│       ├── avaya-test.yml
│       ├── breakconfig.yml
│       ├── configs
│       │   ├── management-SW1.cfg
│       │   ├── management-SW2.cfg
│       │   ├── management-SW3.cfg
│       │   └── management-SW4.cfg
│       ├── group_vars
│       │   ├── Network-Physical.yml
│       │   ├── Routers.yml
│       │   ├── Switches.yml
│       │   └── all.yml
│       ├── host_vars
│       │   └── SW4.yml
│       ├── hosts
│       ├── ntc-test.yml
│       ├── roles
│       │   └── management
│       │       ├── defaults
│       │       ├── files
│       │       ├── handlers
│       │       ├── tasks
│       │       │   └── main.yml
│       │       ├── templates
│       │       │   ├── Network-Physical.j2
│       │       │   ├── aaa.j2
│       │       │   ├── snmp.j2
│       │       │   └── ssh.j2
│       │       └── vars
│       │           └── main.yml
│       ├── show_output.yml
│       ├── snmp_facts.yml
│       └── templates
├── ansible-requirements.txt
└── install-environment.sh

**Variable Precedence**

It is important to know the variable precedence to understand how to structure each playbook. Below is the precedence as of Ansible 2.3.x

 | PRECEDENCE |      VARIABLE NAME      |           COMMON LOCATION          |
 |------------|-------------------------|------------------------------------|
 | 1.         | Inventory Vars          | Inventory file [all:vars]          |
 | 2.         | Inventory Group_Vars    | Inventory file [group:vars]        |
 | 3.         | Inventory Host_Vars     | Inventory file [host:vars]         |
 | 4.         | Playbook All vars       | /vars/                             |
 | 5.         | Playbook Group_Vars     | /group_vars/                       |
 | 6.         | Playbook Host_Vars      | /host_vars/                        |
 | 7.         | Host Facts              | Playbook -  gather_facts module    |
 | 8.         | Registered Vars         | Playbook - register module         |
 | 9.         | Set_Facts               | Playbook - set_fact module.        |
 | 10.        | Play vars               | Defined within playbook            |
 | 11.        | Play vars_prompt        | Defined within playbook            |
 | 12.        | Play vars_files         | Defined within playbook            |
 | 13.        | Role and include vars   | /roles/ and within playbook        |
 | 14.        | Block vars              | Playbook - block module            |
 | 15.        | Task vars               | Defined within playbook            |
 | 16.        | Extra vars              | --extra-vars - adhoc command       |

**Network Vendors support**

The following is a list of the network vendors that are currently or will be included in the future with these playbooks.

 |  Vendor/OS      |   Status      |
 |-----------------|---------------|
 | Cisco IOS/XE    | Available     |
 | Cisco IOS-XR    | Not Projected |
 | Cisco NX-OS     | Projected     |
 | Arista vEOS     | In Progress   |
 | Cumulus VX      | In Progress   |
 | HP (Any)        | Not Projected |
 | Brocade (Any)   | Unsure        |
 | Avaya ERS       | Available     |
 | Avaya VSP       | Projected     |
 | Junos           | Projected     |
 | Riverbed RiOS   | Desired       |
 | Citrix Netscaler| Desired       |

- Available: A playbook exists

- Not Projected: Nothing completed and nothing planning to be done

- Projected: Plans to be written, but not a current task

- In progress: In a particular stage of development

- Unsure: Thoughts of writing a playbook, but unsure if necessary

- Desired: Little support from the community. Would require extensive efforts on the backend.

**Playbook Examples**

- Template rendering of network configurations

- SNMP facts

- Show output parsing to a SQL file (Using ntc-ansible's TextFSM feature)

- Roles for modular Playbook implementation

**Future Vision Feature sets**

- NAPALM playbooks
 
  + Diff capabilities

  + Configuration pushes

  + Configuration Backups

- Topology maps

- Further development of roles

- AWX OR Ara integration. Not sure which yet