import json
import os
import subprocess

from cleanup import NewsCleaner

CONFIG_PATH = "config.json"

def restart_program():
    subprocess.run(["systemctl", "restart", "tg_news.service"])

def update_config(new_data):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    config.update(new_data)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    return config

def clean_all():
    cleaner = NewsCleaner()
    cleaner.remove_old_news(0)
    cleaner.close()
    for root, dirs, files in os.walk("media"):
        for file in files:
            os.remove(os.path.join(root, file))
