# Stigmatize for Stigma

This project compliments Stigma: [https://github.com/fmresearchnovak/stigma](https://github.com/fmresearchnovak/stigma).  It aims to automate the process of acquiring APKs and running Stigma on them.

## Installation:
**Assuming a working [Stigma](https://github.com/fmresearchnovak/stigma) environment on linux:**
1. Copy stigmatize.py, app_id_script.js, and package.json to Stigma directory:
    ```bash
    cp stigmatize.py <stigma_directory>
    cp app_id_script.js <stigma_directory>
    cp package.json <stigma_directory>
    ```
2. Install termcolor for colored output:
    ```bash
    pip install termcolor
    ```
3. Install [apkeep](https://github.com/EFForg/apkeep) with [cargo](https://rustup.rs/):
    ```bash
    cargo install apkeep
    ```
    *3.a. You may have to install `libssl-dev` first.*
    *3.b. You may have to add `~/.cargo/bin` to your PATH to be able to run the installed binaries*
    
4. Install required node packages:
    ```bash
    npm install
    ```
    *4.a. You may have to install `npm` first.*

5. Download [Android Studio](https://developer.android.com/studio)
6. Inside android studio, install cmdline-tools via Tools ⇨ SDK Manager ⇨ SDK Tools ⇨ Check the Android SDK Commandline Tools and hit apply
7. *Optional*: Set `$ANDROID_HOME` as an environment variable (defaults to `~/Android/Sdk`)
    

## Usage:
To run the program simply do `python stigmatize.py Instagram` from the Stigma directory.

**Note:** You do not need to input a proper android app package name / id (e.g. "com.instagram.android"), only the name (e.g. Instagram") is necessary.

## Contributors:
- Ed Novak (author of [Stigma](https://github.com/fmresearchnovak/stigma))
- Jake Fulford

