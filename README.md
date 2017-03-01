# ansible-task-firewall
a firewall strategy-plugin for Ansible, to halt play executing when SecOps policy is violated.

## summary
In regulated corporate environments it is a challenge to introduce production automation with Ansible, particularly to overcome security concerns.   One significant concern is that the Ansible/Tower environment (ssh access, sudo without a password) doesn't have any real controls over *what* is run against hosts.   

This firewall strategy plugin provides that control.   Security policy is written in yaml, and consumed and implemented during playbook exection.   Any task violating the policy causes the playbook execution to halt.

## scenario one

SecOps want to prevent arbitrary commands being run on hosts.   This is fairly simple, we can block the modules which allow command/script execution.

```
# /etc/ansible/firewall_policy.yml

# prevent these modules being used
command:
script:
shell:
```

## scenario two

If we want to block a particular argument of a module, we can.   Say we allow user creation, but any Ansible-created users must use ssh keys and not passwords for login.

```
# /etc/ansible/firewall_policy.yml

# prevent the password argument, of the user module, being used
user:
  password:
```

## scenario three

Where things get interesting us when we can run rules against argument values.   There are many modules which operate at the root privilege level.   Because we know mistakes happen, we can implement some protection in our security policy.

```
# /etc/ansible/firewall_policy.yml

# prevent free text sql statements which contain 'drop' or 'system'
oracle_sql:
  sql:
    - contains drop
    - contains system
```

## the plugin

This strategy plugin for Ansible is intended to improve the Ansible story around security.   The policy is written in yaml, and I foresee it being managed by a SecOps team.   Security can be enforced at point-of-execution, no matter how long ago a playbook was committed to the production repo.

Running as a strategy plugin, it can be used in dev, test and prod.   There's not much to setup, and negligable overhead.   But this gives DevOps engineers instant feedback on the compliance of their playbooks.

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
checking firewall rule: [yum:name httpd]
checking firewall rule: [yum:name tcpdump]
ok: [34.248.225.230]

TASK [openldap : install openldap-servers package] *****************************
checking firewall rule: [yum:name httpd]
checking firewall rule: [yum:name tcpdump]
ok: [34.248.225.230]

TASK [openldap : install openldap-clients package] *****************************
checking firewall rule: [yum:name httpd]
checking firewall rule: [yum:name tcpdump]
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
checking firewall rule: [yum:name httpd]
checking firewall rule: [yum:name tcpdump]
ERROR! firewall policy: module (yum) arg (name) value (tcpdump) blocked
```

# TODO
The Ansible execution flow gets quite complicated around variables, conditionals, and includes.   So I am still working on how to correctly parse the hierarchy of variables and includes.   This means that a simple workaround for the 'contains drop' rule above is to store the command arg in a variable.   This could be countered by disabling variables on certain arguments, but that's not good Ansible practice.

