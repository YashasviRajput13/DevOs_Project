import urllib.request
import json

def get_repos():
    try:
        res = urllib.request.urlopen("http://localhost:8000/api/projects")
        projects = json.loads(res.read().decode('utf-8'))
        for p in projects:
            print(f"Project {p['id']}: {p['name']}")
            res2 = urllib.request.urlopen(f"http://localhost:8000/api/projects/{p['id']}/repositories")
            repos = json.loads(res2.read().decode('utf-8'))
            for r in repos:
                print(f"  Repo {r['id']}: {r['name']} - indexed: {r['indexed']}")
                
                # test arch
                try:
                    arch_res = urllib.request.urlopen(f"http://localhost:8000/api/projects/{p['id']}/repositories/{r['id']}/architecture")
                    print(f"    Arch ok, len {len(arch_res.read().decode('utf-8'))}")
                except urllib.error.HTTPError as e:
                    print(f"    Arch error: {e.code} {e.read().decode('utf-8')}")
                
                # test chat
                try:
                    req = urllib.request.Request(
                        'http://localhost:8000/api/chat',
                        data=json.dumps({"query": "architecture of the project", "project_id": p['id'], "repository_id": r['id']}).encode('utf-8'),
                        headers={'Content-Type': 'application/json'},
                    )
                    chat_res = urllib.request.urlopen(req)
                    print(f"    Chat ok, len {len(chat_res.read().decode('utf-8'))}")
                except urllib.error.HTTPError as e:
                    print(f"    Chat error: {e.code} {e.read().decode('utf-8')}")
                    
    except Exception as e:
        print("API Error", e)

get_repos()
