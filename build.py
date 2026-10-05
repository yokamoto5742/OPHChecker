import subprocess


def build_executable():
    subprocess.run([
        "pyinstaller",
        "--name=眼科手術指示確認",
        "--windowed",
        "--icon=assets/OPHChecker.ico",
        "--add-data", "utils/config.ini:.",
        # openpyxlが任意でimportするnumpy/pandasが環境にあっても同梱しない
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "main.py"
    ])

    print(f"Executable built successfully.")


if __name__ == "__main__":
    build_executable()
