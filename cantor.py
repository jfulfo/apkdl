"""
Cantor: Job Runner for Alpha Server

Purpose: Interfaces with alpha server to run arbitrary jobs via ssh.
Jobs are abstract, simply a list of commands and a name.
It is expected that the user will write their own scripts to decide the commands.

Author: Jade
"""

import os
import sys
import time 
import paramiko
from termcolor import cprint
import concurrent.futures
import getpass
from tqdm import tqdm

class Job:
    """Job object to be run on alpha server"""
    def __init__(self, name, commands, server, username, password):
        self.name = name
        self.commands = commands
        self.server = server
        self.username = username
        self.password = password

    def run(self):
        """Runs job on alpha server"""
        cprint(time.strftime("%H:%M:%S"), "cyan", attrs=["bold"], end=" ")
        cprint(f"Starting job: {self.name}", "green", attrs=["bold"])
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.server, username=self.username, password=self.password)
        for command in tqdm(self.commands, desc=f"{self.name} progress"):
            stdin, stdout, stderr = ssh.exec_command(command)
            for line in stdout:
                cprint(f"{self.username}@{self.server}>{command}: ", "green", attrs=["bold"], end="")
                cprint(line, "white", end="")
            for line in stderr:
                cprint(line, "red", attrs=["bold"])
        ssh.close()

def main():
    """Takes a file of jobs and runs them on alpha server"""
    if len(sys.argv) < 4:
        print("Usage: python3 cantor.py <jobfile> <username> <server>")
        sys.exit(1)
    jobfile = sys.argv[1]
    username = sys.argv[2]
    server = sys.argv[3]
    password = getpass.getpass(prompt='Password: ', stream=None)
    jobs = []
    with open(jobfile, "r") as f:
        job_data = f.read().split('---')
        for job_commands in job_data:
            commands = [cmd for cmd in job_commands.split('\n') if cmd]
            job_name = commands.pop(0)
            jobs.append(Job(job_name, commands, server, username, password))
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda job: job.run(), jobs)

if __name__ == "__main__":
    main()

