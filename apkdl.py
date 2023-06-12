import os
import sys
import subprocess
import json
import paramiko
import concurrent.futures
from termcolor import cprint

# configuration
SSH_USER = "jade"
SSH_SERVER = "alpha"
SSH_PASSWORD = "jade"
PROCESS_SCRIPT_PATH = "stigma.py"
APK_DIRECTORY = "./apks"

def ssh_connect(user, server, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, username=user, password=password)
    return ssh

def get_app_id(ssh, query):
    stdin, stdout, stderr = ssh.exec_command(f"node app_id_script.js \"{query}\"")
    if stderr.readlines():
        cprint(f"Error getting app id for {query}", "red", attrs=["bold"])
        return None
    result = json.loads(stdout.read())
    return result[0]["appId"] if result else None

def download_files(ssh, apps):
    for app in apps:
        app_id = get_app_id(ssh, app)
        if app_id:
            cprint(f"Found app: {app}", "green", attrs=["bold"])
            cprint("Downloading with apkeep...", "cyan", attrs=["bold"])
            ssh.exec_command(f"apkeep -a {app_id} .")
            stdout.channel.recv_exit_status()  # ensure the command completes

            # detect if xapk
            stdin, stdout, stderr = ssh.exec_command(f"ls {APK_DIRECTORY}/{app_id}.xapk 2> /dev/null")
            if stdout.readlines():
                cprint(f"XAPK detected for {app}!", "yellow", attrs=["bold"])
                cprint("Extracting...", "cyan", attrs=["bold"])
                ssh.exec_command(f"unzip {APK_DIRECTORY}/{app_id}.xapk -d {APK_DIRECTORY}/{app_id}")
                ssh.exec_command(f"mv -v {APK_DIRECTORY}/{app_id}/{app_id}.apk {APK_DIRECTORY}/{app_id}.apk")
                ssh.exec_command(f"rm -rf {APK_DIRECTORY}/{app_id} {APK_DIRECTORY}/{app_id}.xapk")

            cprint(f"Done with {app}!", "green", attrs=["bold"])
        else:
            cprint(f"No app found for {app}", "red", attrs=["bold"])

def get_files(ssh):
    stdin, stdout, stderr = ssh.exec_command(f"ls {APK_DIRECTORY}/*.apk")
    files = stdout.readlines()
    return files

def process_file(file):
    ssh = ssh_connect(SSH_USER, SSH_SERVER, SSH_PASSWORD)
    cprint(f"Processing {file.strip()}...", "cyan", attrs=["bold"])
    ssh.exec_command(f"python3 {PROCESS_SCRIPT_PATH} {file.strip()}")
    stdout.channel.recv_exit_status()  # ensure the command completes
    ssh.close()

def main():
    ssh = ssh_connect(SSH_USER, SSH_SERVER, SSH_PASSWORD)

    apps = input("Enter the names of the apps you want to download, separated by comma: ").split(',')
    apps = [app.strip() for app in apps]
    download_files(ssh, apps)

    files = get_files(ssh)

    # create a ProcessPoolExecutor (for parallel processing)
    with concurrent.futures.ProcessPoolExecutor(max_workers=16) as executor:
        executor.map(process_file, files)

    ssh.close()

if __name__ == "__main__":
    main()

