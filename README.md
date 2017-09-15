# Ansible Playbooks (Linux and Network Vendors)
## Version 1.0

An array of Ansible playbooks in the making for the benefit of automating all the things (Or those that should be).

Built in python 2.7, although will be migrated to python 3.6 soon due to nearing EOS state of 2.7.

These playbooks are constructed in a manner that aligns as close to "Best practice" as possible. For more details on Ansible best practice file structure, visit Ansible's website, or view the "playbook-build-example" file.

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