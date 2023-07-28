import requests
import zipfile
import io
import os

DATA_FILE_PATH = "chars.data"


def solve_captcha(captcha):
    chars = get_chars()
    solution = ""
    captcha = captcha[44:]
    while True:
        found = False
        for char, data in chars.items():
            if len(captcha) > len(data) and captcha[:len(data)] == data:
                solution += char
                captcha = captcha[len(data):].lstrip(b"\x00")
                found = True
                break
        if not found:
            break
    return solution


def get_chars():
    if os.path.exists(DATA_FILE_PATH):
        with open(DATA_FILE_PATH, "rb") as data_file:
            chars = read_chars_from_file(data_file)
    else:
        chars = download_chars()
        write_chars_to_file(chars)
    return chars


def read_chars_from_file(data_file):
    import pickle
    dec = pickle.Unpickler(data_file)
    chars = dec.load()
    return chars


def write_chars_to_file(chars):
    with open(DATA_FILE_PATH, "wb") as data_file:
        import pickle
        enc = pickle.Pickler(data_file)
        enc.dump(chars)


def download_chars():
    char_recordings_url = "https://web.archive.org/web/20170625020320/http://www.phpcaptcha.org/downloads/audio/securimage_audio-de.zip"
    chars = {}
    response = requests.get(char_recordings_url)
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data) as zip_file:
        for file in zip_file.namelist():
            char = os.path.splitext(os.path.basename(file))[0]
            if len(char) != 1:
                continue
            with zip_file.open(file) as audio_file:
                data = audio_file.read()[44:]
                chars[char] = data
    return chars
