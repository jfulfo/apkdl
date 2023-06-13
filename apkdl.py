import sys
import subprocess
import json
import concurrent.futures
from termcolor import cprint

# configuration
PROCESS_SCRIPT_PATH = "stigma.py"
APK_DIRECTORY = "./apks"

def get_app_id(query):
    try:
        result = subprocess.check_output(["node", "code/apkdl/app_id_script.js", query], text=True)
        result = json.loads(result)
        return result[0]["appId"] if result else None
    except Exception as e:
        cprint(f"Error getting app id for {query}", "red", attrs=["bold"])
        return None

def download_files(apps):
    for app in apps:
        app_id = get_app_id(app)
        if app_id:
            cprint(f"Found app: {app}", "green", attrs=["bold"])
            cprint("Downloading with apkeep...", "cyan", attrs=["bold"])
            subprocess.run(["apkeep", "-a", app_id, APK_DIRECTORY], check=True)

            file_list = subprocess.check_output(["ls", f"{APK_DIRECTORY}/{app_id}*"], text=True)
            if "xapk" in file_list:
                cprint(f"XAPK detected for {app}!", "yellow", attrs=["bold"])
                cprint("Extracting...", "cyan", attrs=["bold"])
                subprocess.run(["unzip", f"{APK_DIRECTORY}/{app_id}.xapk", "-d", f"{APK_DIRECTORY}/{app_id}"], check=True)
                subprocess.run(["mv", "-v", f"{APK_DIRECTORY}/{app_id}/{app_id}.apk", f"{APK_DIRECTORY}/{app_id}.apk"], check=True)
                subprocess.run(["rm", "-rf", f"{APK_DIRECTORY}/{app_id}", f"{APK_DIRECTORY}/{app_id}.xapk"], check=True)

            cprint(f"Done with {app}!", "green", attrs=["bold"])
        else:
            cprint(f"No app found for {app}", "red", attrs=["bold"])

def get_files():
    file_list = subprocess.check_output(["ls", f"code/Stigma/{APK_DIRECTORY}/*.apk"], text=True)
    files = file_list.split("\n")
    return files

def process_file(file):
    cprint(f"Processing {file.strip()}...", "cyan", attrs=["bold"])
    subprocess.run(["python3", f"code/Stimga/{PROCESS_SCRIPT_PATH}", f"{APK_DIRECTORY}/{file.strip()}"], check=True)

def main():
    apps = input("Enter the names of the apps you want to download, separated by comma: ").split(',')
    apps = [app.strip() for app in apps]
    download_files(apps)

    files = get_files()

    # create a ProcessPoolExecutor (for parallel processing)
    with concurrent.futures.ProcessPoolExecutor(max_workers=16) as executor:
        executor.map(process_file, files)

if __name__ == "__main__":
    main()

