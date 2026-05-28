# Project Title

> ⚠️ **Note:** This is a one-man project. There may be some unforeseen bugs and errors. If you encounter any issues, please send an email to **sandeshalt111@gmail.com** and I will try to fix them as soon as possible.

## Prerequisites

To run this project, you need to have **Python** installed along with all the dependencies listed in the `requirements.txt` file.

### 1. Install Dependencies
After downloading the `requirements.txt` file, run the following command in your terminal to install everything you need:

```bash
pip install -r requirements.txt
```
### 2. Building the Executable (.exe)
You can compile the script into a standalone executable file using PyInstaller.

If you want the original icon included in the executable, make sure you download icon.ico and place it in the same directory, then run:

```bash
pyinstaller --onefile --windowed --icon=icon.ico browser3.py
```
Note: If you want to compile older versions of the script into an .exe, simply change browser3.py in the command above to browser2.py or browser.py depending on the file you want to build.
