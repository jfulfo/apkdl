"""
Stigmatize.py
- Automates the process of downloading and running apks through Stigma
- Emulates the apk and outputs the logcat

See https://github.com/jfulfo/stigmatize 
"""
import os
import sys
import subprocess
from subprocess import CalledProcessError
from multiprocessing import Process
import json
import concurrent.futures
from termcolor import cprint
from time import sleep

# configuration
ANDROID_HOME = ""
STIGMA_PATH = "./Stigma.py"
APK_PATH = "./apks"
MODIFIED_APK_PATH = "./modified"
DEBUG = True

def ask_continue():
    cprint("Continue? (Y/n)", "yellow", attrs=["bold"])
    answer = input().lower()
    if answer == "n":
        cprint("Exiting...", "red", attrs=["bold"])
        sys.exit()

# uses nodejs to get app id from query
def get_app_id(query):
    try:
        result = subprocess.check_output(["node", "./app_id_script.js", query], text=True)
        result = json.loads(result)
        return result[0]["appId"] if result else None
    except Exception as e:
        cprint(f"Error getting app id for {query}", "red", attrs=["bold"])
        return None

# checks if app already exists in apk directory
def app_exists(app_id):
    if app_id in subprocess.check_output(["ls", f"{APK_PATH}"], text=True):
        cprint(f"{app_id} already exists in {APK_PATH}", "yellow", attrs=["bold"])
        cprint("Skipping download...", "yellow", attrs=["bold"])
        return True
    else:
        return False

def extract_xapk(app_id):
    if os.path.exists(f"{APK_PATH}/{app_id}.xapk"):
        cprint(f"XAPK detected for {app_id}", "yellow", attrs=["bold"])
        cprint("Extracting...", "green", attrs=["bold"])
        subprocess.run(["unzip", f"{APK_PATH}/{app_id}.xapk", "-d", f"{APK_PATH}/{app_id}"], check=True)
        subprocess.run(["mv", "-v", f"{APK_PATH}/{app_id}/{app_id}.apk", f"{APK_PATH}/{app_id}.apk"], check=True)
        subprocess.run(["rm", "-rf", f"{APK_PATH}/{app_id}", f"{APK_PATH}/{app_id}.xapk"], check=True)
    else:
        cprint("No XAPK detected", "green", attrs=["bold"])

# uses apkeep to download apk
def download_apk(app):
    app_id = get_app_id(app)
    if not app_id:
        cprint(f"Error getting app id for {app}", "red", attrs=["bold"])
        return

    cprint(f"Found app: {app}", "green", attrs=["bold"])

    if app_exists(app_id): 
        return

    cprint("Downloading with apkeep...", "green", attrs=["bold"])
    subprocess.run(["apkeep", "-a", app_id, APK_PATH], check=True)

    # check if xapk file
    extract_xapk(app_id)

    cprint(f"Done downloading {app}", "green", attrs=["bold"])

# delete apks in apk directory
def delete_apks():
    cprint("Would you like to delete the downloaded apks? (Y/n)", "yellow", attrs=["bold"], end=" ")
    answer = input().lower()
    if answer == "y" or answer == "":
        cprint("Deleting apks...", "green", attrs=["bold"])
        subprocess.run([f"rm -rf {APK_PATH}/*"], shell=True, check=True)

# process apk with Stigma
def process_apk(apk):
    cprint(f"Stigmatizing {apk}...", "green", attrs=["bold"])
    try:
        if DEBUG: # nothing suppressed
            subprocess.run(f"echo '\\n' | python3 {STIGMA_PATH} {APK_PATH}/{apk}", shell=True, check=True)
        else: # log stdout but keep stderr
            subprocess.run(f"echo '\\n' | python3 {STIGMA_PATH} {APK_PATH}/{apk}", stdout=open(f"stigma_{apk}.log", w), shell=True, check=True)

        subprocess.run(["mv", f"Modified_{apk}", f"{MODIFIED_APK_PATH}"])
        cprint(f"\nStigmatized {apk}", "green", attrs=["bold"])
        return True
    except CalledProcessError as e:
        cprint(f"Error processing {apk}", "red", attrs=["bold"])
        cprint(e.output, "red", attrs=["bold"])
        return False

def wait_for_emulator():
    boot_completed = None
    timeout = 30
    while boot_completed != "stopped" and timeout > 0:
        boot_completed = subprocess.check_output([f"{ANDROID_HOME}/platform-tools/adb", "shell", "getprop", "init.svc.bootanim"]).decode().strip()
        sleep(1)  # Wait a bit before polling again
        timeout -= 1
    if timeout == 0:
        cprint("Emulator failed to boot!", "red", attrs=["bold"])
        return False
    return True

def start_emulator():
    if DEBUG:
        subprocess.run([f"{ANDROID_HOME}/emulator/emulator", "-avd", "stigma"], check=True)
    else:
        subprocess.run([f"{ANDROID_HOME}/emulator/emulator", "-avd", "stigma"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# logcat thread filtered by "stigma"
def start_logcat():
    if DEBUG:
        subprocess.run([f"{ANDROID_HOME}/platform-tools/adb", "logcat", "stigma:*", "Stigma:*", "*:S"])
    else:
        subprocess.run([f"{ANDROID_HOME}/platform-tools/adb", "logcat", "stigma:*", "Stigma:*", "*:S"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# launch emulator and logcat threads
def emulate(apk):
    cprint(f"Emulating {apk}...", "green", attrs=["bold"])
    emulator_process = Process(target=start_emulator)
    emulator_process.start()
    cprint("Waiting for emulator to boot...", "yellow", attrs=["bold"])
    sleep(5)
    if not wait_for_emulator():
        emulator_process.terminate()
        ask_continue()
        return
    logcat_process = Process(target=start_logcat)
    logcat_process.start()

    # the adb install might error, if so print the error and kill threads
    cprint (f"Installing {apk} with adb...", "green", attrs=["bold"])
    try:
        subprocess.run([f"{ANDROID_HOME}/platform-tools/adb", "install", "-r", f"{MODIFIED_APK_PATH}/{apk}"], check=True)
    except CalledProcessError as e:
        cprint(f"Error installing {apk}", "red", attrs=["bold"])
        cprint(e.output, "red", attrs=["bold"])
        emulator_process.terminate()
        logcat_process.terminate()
        ask_continue()
        return

    cprint(f"Installed {apk}", "green", attrs=["bold"])
    cprint(f"Launching {apk}...", "green", attrs=["bold"])
    subprocess.run([f"{ANDROID_HOME}/platform-tools/adb", "shell", "monkey", "-p", f"{apk[:-4]}", "-c", "android.intent.category.LAUNCHER", "1"], check=True)

    cprint(f"Emulating {apk} for 30 seconds...", "green", attrs=["bold"])
    sleep(30)
    emulator_process.terminate()
    logcat_process.terminate()

def main():
    # check if ANDROID_HOME is set
    try:
        ANDROID_HOME = os.environ["ANDROID_HOME"]
    except KeyError:
        cprint("ANDROID_HOME environment variable not set", "red", attrs=["bold"])
        cprint("Input path to Android SDK (e.g. '~/Android/Sdk'): ", "yellow", attrs=["bold"], end="")
        ANDROID_HOME = input()
        if ANDROID_HOME == "":
            cprint("Defaulting to '~/Android/Sdk'", "green", attrs=["bold"])
            ANDROID_HOME = "~/Android/Sdk"
        else:
            cprint(f"Using {ANDROID_HOME}", "green", attrs=["bold"])

    # set apps
    if len(sys.argv) > 1:
        cprint("Using command line arguments as app list", "green", attrs=["bold"])
        apps = sys.argv[1:]
    else:
        cprint("Enter the names of the apps you want to download, separated by comma:", "green", attrs=["bold"], end=" ")
        apps = input().split(",")
        apps = [app.strip() for app in apps]

    if not os.path.exists(f"{APK_PATH}"):
        subprocess.run(["mkdir", f"{APK_PATH}"])
        cprint("Created apk directory", "green", attrs=["bold"])

    if not os.path.exists(f"{MODIFIED_APK_PATH}"):
        subprocess.run(["mkdir", f"{MODIFIED_APK_PATH}"])
        cprint("Created modified apk directory", "green", attrs=["bold"])

    for app in apps:
        download_apk(app)

    apks = os.listdir(APK_PATH)

    # create a ProcessPoolExecutor (for parallel processing)
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        executor.map(process_apk, apks)

    modified_apks = os.listdir(MODIFIED_APK_PATH)

    # check if "stigma" avd exists with avdmanager
    if "stigma" not in subprocess.check_output([f"{ANDROID_HOME}/cmdline-tools/latest/bin/avdmanager", "list", "avd"], text=True):
        cprint("Stigma avd not found, creating...", "yellow", attrs=["bold"])
        subprocess.run([f"{ANDROID_HOME}/cmdline-tools/latest/bin/sdkmanager", "system-images;android-29;google_apis;x86"], check=True)
        subprocess.run([f"{ANDROID_HOME}/cmdline-tools/latest/bin/avdmanager", "create", "avd", "-n", "stigma", "-k", "system-images;android-29;google_apis;x86", "-d", "pixel_3a"], check=True)

    try:
        for apk in modified_apks:
            emulate(apk)
    except Exception as e:
        cprint(e, "red", attrs=["bold"])

    delete_apks()
    cprint("Done", "green", attrs=["bold"])

if __name__ == "__main__":
    main()

