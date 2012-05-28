#!/usr/bin/env python

# Copyright 2010 University of Chicago
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Demonstrate API calls.

Example run using standard globus toolkit certificate locations:

python example.py USERNAME -k ~/.globus/userkey.pem -c ~/.globus/usercert.pem
"""
import time
from datetime import datetime, timedelta
import traceback

from globusonline.transfer.api_client import Transfer, create_client_from_args
from globusonline.transfer.api_client import ActivationRequirementList

# TransferAPIClient instance.
api = None

def tutorial():
    """
    Do a bunch of API calls and display the results. Does a small transfer
    between tutorial endpoints, but otherwise does not modify user data.

    Uses module global API client instance.
    """
    # See what is in the account before we make any submissions.
    #print "=== Before tutorial ==="
    #display_tasksummary(); print
    #display_task_list(); print
    #display_endpoint_list(); print

    print "=== Before transfer ==="
    # auto activate the endpoint, and display before/after.
    #display_activation("go#ep1")
    #display_activation("go#ep2")
    site_ep1 = "cin0641a#irods-dev"
    site_ep2 = "cin0641a#GSI-PLX"
    site_username = "cin0641a"
    api.set_debug_print(False, True)
    #status, message, data = api.endpoint_autoactivate("go#ep1")
    status, message, data = api.endpoint_autoactivate(site_ep1)
    #data = {
                 #"DATA_TYPE": "activation_requirements",
                 #"type": "myproxy",
                 #"name": "username",
		 #"description": "null",
		 #"canonical_name": "null",
		 #"public": "null",
		 #"is_globus_connect": "null",
               #}
    #data = ActivationRequirementList(data)


    print "=== Activate endpoints ==="
    data.set_requirement_value("myproxy", "username", site_username)
    from getpass import getpass
    passphrase = getpass()
    data.set_requirement_value("myproxy", "passphrase", passphrase)
    #status, message, data = api.endpoint_activate(site_ep, data)
    #data["code"]
    api.endpoint_activate(site_ep1, data)
    api.endpoint_activate(site_ep2, data)
    #status, message, data = api.endpoint_activate(site_ep2, data)
    #data["code"]
    #display_activation("cin0641a#irods-dev")
    #display_ls("cin0641a#irods-dev"); print
    #display_activation("cin0641a#vzSARA")

    #display_ls("go#ep1"); print
    #display_ls("go#ep2"); print
    #display_ls("cin0641a#vzSARA"); print
    #display_activation("cin0641a#GSI-PLX")
    #display_ls("cin0641a#GSI-PLX"); print

    print "=== Prepare transfer ==="
    #raw_input("Press Enter to continue...")
    # submit a transfer
    code, message, data = api.transfer_submission_id()
    submission_id = data["value"]
    deadline = datetime.utcnow() + timedelta(minutes=10)
    t = Transfer(submission_id, site_ep1, site_ep2, deadline)
    t.add_item("/CINECA/home/gmariani/go-test/some-file/1", "/plx/userprace/pr1is019/tmp/1")
    t.add_item("/CINECA/home/gmariani/go-test/some-file/2", "/plx/userprace/pr1is019/tmp/2")
    t.add_item("/CINECA/home/gmariani/go-test/some-file/3", "/plx/userprace/pr1is019/tmp/3")
    t.add_item("/CINECA/home/gmariani/go-test/some-file/4", "/plx/userprace/pr1is019/tmp/4")
    print "=== Submit transfer ==="
    code, reason, data = api.transfer(t)
    task_id = data["task_id"]

    # see the new transfer show up
    #print "=== After submit ==="
    #display_tasksummary(); print
    #display_task(task_id); print
    #raw_input("Press Enter to continue...")

    # wait for the task to complete, and see the summary and lists
    # update
    print "=== Checking completion ==="
    wait_for_task(task_id)
    #if wait_for_task(task_id):
        #display_tasksummary(); print
        #display_task(task_id); print
        #display_ls("cin0641a#GSI-PLX"); print
    print "=== Deactivate endpoint ==="
    api.endpoint_deactivate(site_ep1)
    api.endpoint_deactivate(site_ep2)


def display_activation(endpoint_name):
    print "=== Endpoint pre-activation ==="
    display_endpoint(endpoint_name)
    print
    code, reason, result = api.endpoint_autoactivate(endpoint_name,
                                                     if_expires_in=600)
    if result["code"].startswith("AutoActivationFailed"):
        print "Auto activation failed, ls and transfers will likely fail!"
    print "result: %s (%s)" % (result["code"], result["message"])
    print "=== Endpoint post-activation ==="
    display_endpoint(endpoint_name)
    print


def display_tasksummary():
    code, reason, data = api.tasksummary()
    print "Task Summary for %s:" % api.username
    for k, v in data.iteritems():
        if k == "DATA_TYPE":
            continue
        print "%3d %s" % (int(v), k.upper().ljust(9))


def display_task_list(max_age=None):
    """
    @param max_age: only show tasks requested at or after now - max_age.
    @type max_age: timedelta
    """
    kwargs = {}
    if max_age:
        min_request_time = datetime.utcnow() - max_age
        # filter on request_time starting at min_request_time, with no
        # upper limit on request_time.
        kwargs["request_time"] = "%s," % min_request_time

    code, reason, task_list = api.task_list(**kwargs)
    print "task_list for %s:" % api.username
    for task in task_list["DATA"]:
        print "Task %s:" % task["task_id"]
        _print_task(task)

def _print_task(data, indent_level=0):
    """
    Works for tasks and subtasks, since both have a task_id key
    and other key/values are printed by iterating through the items.
    """
    indent = " " * indent_level
    indent += " " * 2
    for k, v in data.iteritems():
        if k in ("DATA_TYPE", "LINKS"):
            continue
        print indent + "%s: %s" % (k, v)

def display_task(task_id, show_subtasks=True):
    code, reason, data = api.task(task_id)
    print "Task %s:" % task_id
    _print_task(data, 0)

    if show_subtasks:
        code, reason, data = api.subtask_list(task_id)
        subtask_list = data["DATA"]
        for t in subtask_list:
            print "  subtask %s:" % t["task_id"]
            _print_task(t, 4)

def wait_for_task(task_id, timeout=120):
    status = "ACTIVE"
    while timeout and status == "ACTIVE":
        code, reason, data = api.task(task_id, fields="status")
        status = data["status"]
        time.sleep(1)
        timeout -= 1

    if status != "ACTIVE":
        print "Task %s complete!" % task_id
        return True
    else:
        print "Task still not complete after %d seconds" % timeout
        return False

def display_endpoint_list():
    code, reason, endpoint_list = api.endpoint_list(limit=100)
    print "Found %d endpoints for user %s:" \
          % (endpoint_list["length"], api.username)
    for ep in endpoint_list["DATA"]:
        _print_endpoint(ep)

def display_endpoint(endpoint_name):
    code, reason, data = api.endpoint(endpoint_name)
    _print_endpoint(data)

def _print_endpoint(ep):
    name = ep["canonical_name"]
    print name
    if ep["activated"]:
        print "  activated (expires: %s)" % ep["expire_time"]
    else:
        print "  not activated"
    if ep["public"]:
        print "  public"
    else:
        print "  not public"
    if ep["myproxy_server"]:
        print "  default myproxy server: %s" % ep["myproxy_server"]
    else:
        print "  no default myproxy server"
    servers = ep.get("DATA", ())
    print "  servers:"
    for s in servers:
        uri = s["uri"]
        if not uri:
            uri = "GC endpoint, no uri available"
        print "    " + uri,
        if s["subject"]:
            print " (%s)" % s["subject"]
        else:
            print

def unicode_(data):
    """
    Coerce any type to unicode, assuming utf-8 encoding for strings.
    """
    if isinstance(data, unicode):
        return data
    if isinstance(data, str):
        return unicode(data, "utf-8")
    else:
        return unicode(data)

def display_ls(endpoint_name, path=""):
    code, reason, data = api.endpoint_ls(endpoint_name, path)
    # Server returns canonical path; "" maps to the users default path,
    # which is typically their home directory "/~/".
    path = data["path"]
    print "Contents of %s on %s:" % (path, endpoint_name)
    headers = "name, type, permissions, size, user, group, last_modified"
    headers_list = headers.split(", ")
    print headers
    for f in data["DATA"]:
        print ", ".join([unicode_(f[k]) for k in headers_list])

if __name__ == '__main__':
    api, _ = create_client_from_args()
    tutorial()
