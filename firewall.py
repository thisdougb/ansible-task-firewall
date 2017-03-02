# file: /usr/lib/python2.7/site-packages/ansible/plugins/strategy/firewall.py

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import cmd
import sys
import yaml
import pprint

from ansible.plugins.strategy.linear import StrategyModule as LinearStrategyModule
from ansible.errors import AnsibleError

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class StrategyModule(LinearStrategyModule):
    def __init__(self, tqm):

        # NOTE: hard coded because, being a firewall, this should not
        #       be overriden by a local ansible.cfg var.   Still feels
        #       a dirty way to do it.
        self.firewall = Firewall('/etc/ansible/firewall_policy.yml')

        self.curr_tqm = tqm
        super(StrategyModule, self).__init__(tqm)

    def _queue_task(self, host, task, task_vars, play_context):
        self.curr_host = host
        self.curr_task = task
        self.curr_task_vars = task_vars
        self.curr_play_context = play_context

        # call firewall check, which will reject on failure
        self.firewall.reject_task(self.curr_task, self.curr_task_vars)

        # task passed the firewall check, run as usual
        super(StrategyModule, self)._queue_task(host, task, task_vars, play_context)

class Firewall:
    def __init__(self, firewall_policy_path=None):

       self.policy = {}

       try:
           with open(firewall_policy_path, 'r') as stream:
               self.policy = yaml.load(stream)
       except yaml.YAMLError as exc:
           display.warning('%s badly formatted' % firewall_policy_path)
           raise
       except IOError:
           display.warning('%s missing, no firewall policy will be applied' % firewall_policy_path)
           pass
       else:
           display.v("firewall policy loaded: %s" % firewall_policy_path)


    def reject_task(self, task, task_vars):

        # is the task action capture by our policy?
        if task.action in self.policy:

            # is the entire action blocked?
            if not isinstance(self.policy[task.action], list) and not isinstance(self.policy[task.action], dict):
                raise AnsibleError('firewall policy: module (%s) blocked' % task.action)
            display.v('firewall rule: module [%s]' % (self.policy[task.action]))

            # now check the action args
            for key in self.policy[task.action]:

                if key not in task.args:
                    continue

                # is an entire arg of this action blocked?
                if not isinstance(self.policy[task.action][key], list):
                    raise AnsibleError('firewall policy: module (%s) arg (%s) blocked' % (task.action, key))
                display.v('firewall rule passed: [%s:%s] against %s' % (self.policy[task.action], self.policy[task.action][key], task.args[key]))

                # check if the task arg contains a var that needs to be expanded
                if isinstance(task.args[key], str) and task.args[key].find('\{\{'):
                    # TODO: resolve variables to actual values. This is pretty complicated for an Ansible outsider,
                    #       as I don't want to simply copy/paste/mod the task executor code into here.   It's also 
                    #       pretty essential to the concept of a firewall.
                    pass

                # for each rule in the policy module:arg:[value] list, compare the current task arg
                for rule in self.policy[task.action][key]:

                    # do we have the 'contains' verb option in policy
                    if str(rule).startswith('contains'):
                        if str(task.args[key]).find(rule[9:]) != -1:
                            raise AnsibleError('firewall policy: module (%s) arg (%s) (%s) blocked' % (task.action, key, rule))

                    # check if the policy arg is an exact match for the task arg
                    elif task.args[key] == rule:
                        raise AnsibleError('firewall policy: module (%s) arg (%s) value (%s) blocked' % (task.action, key, rule))

                    display.v('firewall rule passed: [%s:%s %s] against %s' % (task.action, key, rule, task.args[key]))
