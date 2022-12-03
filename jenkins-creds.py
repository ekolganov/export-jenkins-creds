#!/usr/bin/python3
# requirements:
# pip install beautifulsoup4
# pip install hvac

import requests
from bs4 import BeautifulSoup
import re
import os
import glob
import hvac


class RegexpDict(dict):
    def __new__(cls, *args, **kwargs):
        self = dict.__new__(cls, *args, **kwargs)
        self.__dict__ = self
        return self


generate_file_prefix="cred_files"
temp_file = "temp.txt"
jenkins_url="http://your-jenkins.local/script"
jenkins_auth_username = ""
jenkins_auth_token = ""
groovy_script_path = "plain-creds.groovy"
# delimiter in groovy script
delimeter = "-----------------------"

vault_url = "https://my-vault.local/"
vault_token = ""
client = hvac.Client(url=vault_url,token=vault_token)

def write_to_vault(path,data):
    try:
        client.secrets.kv.v2.patch(
            path=f"{path}",
            secret=data,
        )
    except:
        client.secrets.kv.v2.create_or_update_secret(
            path=f"{path}",
            secret=data,
        )
        client.secrets.kv.v2.patch(
            path=f"{path}",
            secret=data,
        )


def parse_jenkins_creds():
    with open(groovy_script_path, 'r') as f:
        data = f.read()
    
    response = requests.post(jenkins_url, auth=(jenkins_auth_username, jenkins_auth_token), data={'script': data})
    parsed_html = BeautifulSoup(response.text, 'html.parser')
    
    # find in html tag pre and in tag text 'class ='
    res_parse = str(parsed_html.body.find(lambda tag: tag.name == "pre" and "class =" in tag.text))
    
    with open(temp_file, 'w+') as f:
        f.write(res_parse)

    return


def prepare_cred_for_vault():
    def _search_text(pattern, text, return_number_group=1):
        res = re.search(pattern, text, re.MULTILINE)
        if res:
            return str(res.group(return_number_group))
        return None


    regexp_patterns = {
        "class_cred": 'class = \".*\.(.*)\"',
        "id": 'id = \"(.*)\"',
        "password": 'password = \"(.*)\"',
        "username": 'username = \"(.*)\"',
        "secret":  'secret = \"(.*)\"',
        # https://regex101.com/r/9jJ3Fo/1
        "private_key": 'privateKey = \"((?:.*\n)+)\"',
        "description": 'description = \"(.*)\"'
    }

    pattern = RegexpDict(regexp_patterns)

    for filename in sorted(glob.iglob(f'{generate_file_prefix}*')):
        password = None
        class_cred = None
        id = None
        username = None
        secret = None
        private_key = None
        description = None
        
        print(filename)
        with open(filename) as file:
            content = file.read()
            
            id = _search_text(pattern.id, content)
            class_cred = _search_text(pattern.class_cred, content)
            description = _search_text(pattern.description, content)
            match class_cred:
                case "StringCredentialsImpl":
                    secret = _search_text(pattern.secret, content)
                    print(f"id: {id}\nsecret: {secret}\ndescription: {description}\n")
                    # write_to_vault(f"your/best/path/jenkins/common", {id: secret})
                case "UsernamePasswordCredentialsImpl":
                    password = _search_text(pattern.password, content)
                    username = _search_text(pattern.username, content)
                    print(f"id: {id}\npassword: {password}\nusername: {username}\ndescription: {description}\n")
                    # write_to_vault(f"your/best/path/jenkins/{id}", {"password": password})
                    # write_to_vault(f"your/best/path/jenkins/{id}", {"username": username})
                case "BasicSSHUserPrivateKey":
                    private_key = _search_text(pattern.private_key, content) 
                    username = _search_text(pattern.username, content)
                    print(f"id: {id}\nprivate_key: {private_key}\nusername: {username}\ndescription: {description}\n")
                    # write_to_vault(f"your/best/path/jenkins/ssh_keys/{id}", {"private_key": private_key})
                    # write_to_vault(f"your/best/path/jenkins/ssh_keys/{id}", {"username": username})
                case "FileCredentialsImpl":
                    print(f"id: {id}\ndescription: {description}")
                case _:
                    print(f"I don't know how to parse class: {class_cred}, check it manual in {temp_file} or {filename}")


def remove_splited_files():
    for file in glob.iglob(f'{generate_file_prefix}*'):
        os.remove(file)


def main():
    parse_jenkins_creds()
    # split a large file into subfiles by delimeter
    os.system("csplit --digits=2 --quiet --prefix=%s %s '/%s/+1' '{*}'" % (generate_file_prefix, temp_file, delimeter)) 
    #prepare_cred_for_vault()
    # remove_splited_files()


if __name__ == "__main__":
    main()