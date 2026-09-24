import subprocess


def pdftotext(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"],
                          check=True, capture_output=True, text=True).stdout
