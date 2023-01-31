# -*- coding: utf8 -*-

""" Module to get ENV vars. """
import os
import subprocess

# Ansible parameters
ANSIBLE_HOSTS_FILE = os.environ.get("ANSIBLE_HOSTS_FILE", '/code/ansible/hosts')
ANSIBLE_PLAYBOOK_FOLDER = os.environ.get("ANSIBLE_PLAYBOOK_FOLDER", '/code/ansible/playbooks')
ANSIBLE_SSHKEY_FOLDER = os.environ.get("ANSIBLE_SSHKEY_FOLDER", '/code/ansible/ssh')

# Discord credentials
DISCORD_GUILD = os.environ.get("DISCORD_GUILD", None)
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_GROUP_ANSIBLE = os.environ.get("DISCORD_GROUP_ANSIBLE", 'ansible')
DISCORD_GROUP_GENERAL = os.environ.get("DISCORD_GROUP_GENERAL", 'iamabot')
DISCORD_GROUP_PCI = os.environ.get("DISCORD_GROUP_PCI", 'public-cloud')
DISCORD_GROUP_PCC = os.environ.get("DISCORD_GROUP_PCC", 'hosted-private-cloud')

# Discord Roles
ROLE_TECH_RO = os.environ.get("DISCORD_ROLE_TECH_RO", "Tech")
ROLE_TECH_RW = os.environ.get("DISCORD_ROLE_TECH_RW", "Tech Lead")
ROLE_ACCOUNTING = os.environ.get("DISCORD_ROLE_ACCOUNTING", "Accounting")

# OVHcloud API credentials
"""
You can generate them here: https://api.ovh.com/createToken/
DO NOT HARDCODE THEM HERE !
They are meant to be passed as ENV vars (secrets) to ensure your safety.
"""
OVH_ENDPOINT = os.environ.get("OVH_ENDPOINT", 'ovh-eu')
OVH_AK = os.environ.get("OVH_APPLICATION_KEY")
OVH_AS = os.environ.get("OVH_APPLICATION_SECRET")
OVH_CK = os.environ.get("OVH_CONSUMER_KEY")

# OVHcloud imageID/flavorId by region
# TODO: fetch it from the API
IMAGE_ID_DATA = {
    "GRA9": {
        "Debian 11": "f56870f7-7d8f-4262-893a-c58ddd2ca0df",
        "Ubuntu 22.10": "4d15695b-9af7-43ea-9d09-5540f25f9c53",
        "Fedora 36": "9e8a8f94-dcfa-4e2f-8a6c-2d93ccac176d",
        },
    "WAW1": {
        "Debian 11": "e83106dd-dde9-4356-8dfe-b5f3d4bc1386",
        "Ubuntu 22.10": "f8825418-ff0c-4a22-8ac0-a6a879b0119b",
        "Fedora 36": "e69b0819-3247-43cc-80d8-59ae60a614cc",
        },
    "UK1": {
        "Debian 11": "afae43cc-199d-4a19-bd0d-aaca3b816ac5",
        "Ubuntu 22.10": "fed14415-118b-4657-8769-9ae5a8e6a433",
        "Fedora 36": "9252dc97-ba02-437d-ab20-3a6dcca1cdc0",
        },
    "BHS1": {
        "Debian 11": "918079fa-d0f1-4b5e-ab68-7b45eb497b6c",
        "Ubuntu 22.10": "878de164-dc98-4a92-bf4f-7c9cbe9f83bc",
        "Fedora 36": "9af65bf8-019a-4240-b1b7-19a34254ec74",
        },
    }
FLAVOR_ID_DATA = {
    "GRA9": {
        "d2-2": "fbb7940b-4268-437c-85f8-8c27fcef0dcd",
        "d2-4": "5085760f-f370-42af-a09a-907b0056ba05",
        "d2-8": "da08411a-14f4-4ce1-842d-ca159a68d834",
        },
    "WAW1": {
        "d2-2": "774a7187-eeb2-4639-92e7-546351cb3eca",
        "d2-4": "743811f0-fc7a-4720-af44-18136493d5a2",
        "d2-8": "9775ffcc-f05f-49f5-9507-a9708cb6f03e",
        },
    "UK1": {
        "d2-2": "d0c3bdf8-c3f7-4e66-8c17-6b21cf4d0a50",
        "d2-4": "3f54312e-984c-45fe-9883-6a4767fff81c",
        "d2-8": "861f84d1-9109-48b0-97e3-9e0d31320013",
        },
    "BHS1": {
        "d2-2": "95ae12e7-e4b4-4710-9c40-7ab207349a0a",
        "d2-4": "93e8b309-aa9c-4666-8edd-d28c96492d15",
        "d2-8": "2f4d65be-f405-4d28-962c-a233e1a02cba",
        },
    }

# We setup some variables for Ansible deployments
SSHKEY_FILE = f'{ANSIBLE_SSHKEY_FOLDER}/id_rsa'
SSHKEY_FILE_PUB = f'{ANSIBLE_SSHKEY_FOLDER}/id_rsa.pub'

if os.path.isfile(SSHKEY_FILE_PUB):
    with open(SSHKEY_FILE_PUB, "r", encoding='utf8') as rsafile:
        LOCAL_SSH_KEY = rsafile.read()
else:
    res = subprocess.run(
        [
            "ssh-keygen",
            f"-f{SSHKEY_FILE}",
            '-N ""',
            ],
        capture_output=True,
        check=True,
        )
    with open(SSHKEY_FILE_PUB, "r", encoding='utf8') as rsafile:
        LOCAL_SSH_KEY = rsafile.read()


USER_DATA_WITH_ANSIBLE=f"""#cloud-config

users:
  - default
  - name: ansible
    groups: sudo
    shell: /bin/bash
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    lock-passwd: true
    ssh-authorized-keys:
        {LOCAL_SSH_KEY}"""