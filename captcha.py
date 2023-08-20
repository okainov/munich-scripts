import requests
import zipfile
import io
import os
import pickle

DATA_FILE_PATH = "chars.data"


def solve_captcha(captcha):
    chars = get_chars()
    captcha = captcha[44:]
    solution = ""
    while True:
        char = next((c for c in chars if captcha.startswith(chars[c])), None)
        if char is None:
            break
        solution += char
        captcha = captcha[len(chars[char]) :].lstrip(b"\x00")
    return solution


def get_chars():
    if os.path.exists(DATA_FILE_PATH):
        with open(DATA_FILE_PATH, "rb") as data_file:
            chars = pickle.load(data_file)
    else:
        chars = download_chars()
        with open(DATA_FILE_PATH, "wb") as data_file:
            pickle.dump(chars, data_file)
    return chars


def download_chars():
    char_recordings_url = "https://web.archive.org/web/20170625020320/http://www.phpcaptcha.org/downloads/audio/securimage_audio-de.zip"
    chars = {}
    response = requests.get(char_recordings_url)
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data) as zip_file:
        for file in zip_file.namelist():
            char = os.path.splitext(os.path.basename(file))[0]
            if len(char) == 1:
                with zip_file.open(file) as audio_file:
                    data = audio_file.read()[44:]
                    chars[char] = data
    return chars
