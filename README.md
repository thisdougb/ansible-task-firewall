# ansible-task-firewall
a firewall strategy-plugin for Ansible, to halt play executing when SecOps policy is violated.

# summary
In regulated corporate environments it is a challenge to bring in automation with Ansible, particularly to overcome security concerns.   One significant problem, in this regard, is that once Ansible/Tower is setup in an environment (ssh access, sudo without a password), there are no checks or controls on the content of playbooks.

From a security perspective, there is nothing to stop DevOps teams creating multiple root accounts for example.   Yes, the counter argument from the Ansible folk is 'pets v cattle.'   But Ansible's opinion simply implies, 'it's your problem, it's up to you to convince your security teams.'   So until we can convince security teams of the 'pets v cattle' argument, we're blocked from really moving on with Ansible in a production environment.

So, I've written a firewall plugin for Ansible, to try and help things along.   Security teams can now write a security policy in yaml, which can enforce things like disabling the command module, or disabling the dump argument of the mysql_db module.   The firewall plugin runs as a strategy, which means you can force all playbook runs through it.

Security policy (potentially a merged set of policy files) can then be implemented as:

```
# /etc/ansible/firewall_policy.yml

# prevent a user being created with uid 0
user:
  uid:
    - 0

# prevent 'password' or 'drop' (sql) in the args to command
command: 
  _raw_params: 
    - contains password
    - contains drop

# disallow the shell module
shell:

# prevent some packages being installed by yum
yum:
  name: 
    - httpd
    - tcpdump
```

And this would look like this in the command line:
```
$ cat build_ldap_server.yml
---
- hosts: tag_Name_ldap
  strategy: firewall

  roles:
    - { role: openldap, tags: ['openldap'] }
    - { role: openldap-config, tags: ['openldap-config'] }



$ ansible-playbook build_ldap_server.yml 

PLAY [tag_Name_ldap] ***********************************************************

TASK [setup] *******************************************************************
ok: [34.248.225.230]

TASK [openldap : install openldap package] *************************************
checking rule: [yum:name httpd] against openldap
checking rule: [yum:name tcpdump] against openldap-clients
ok: [34.248.225.230]

TASK [openldap : install openldap-servers package] *****************************
checking rule: [yum:name httpd] against openldap-servers
checking rule: [yum:name tcpdump] against openldap-clients
ok: [34.248.225.230]

TASK [openldap : install openldap-clients package] *****************************
checking rule: [yum:name httpd] against openldap-clients
checking rule: [yum:name tcpdump] against openldap-clients
ok: [34.248.225.230]

TASK [openldap : logging] ******************************************************
ok: [34.248.225.230]

TASK [openldap : restart rsyslog] **********************************************
changed: [34.248.225.230]

TASK [openldap-config : enable slapd] ******************************************
ok: [34.248.225.230]

TASK [openldap-config : copy base slapd config] ********************************
ok: [34.248.225.230]

TASK [openldap-config :  install tcpdump for debugging] ************************
checking rule: [yum:name httpd] against openldap-config
checking rule: [yum:name tcpdump] against openldap-config
ERROR! firewall policy: module (yum) arg (name) value (tcpdump) blocked
```

# TODO
The Ansible execution flow gets quite complicated around variables, conditionals, and includes.   So I am still working on how to correctly parse the hierarchy of variables and includes.   This means that a simple workaround for the 'contains drop' rule above is to store the command arg in a variable.   This could be countered by disabling variables on certain arguments, but that's not good Ansible practice.

