import pathlib
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILE_PATH = REPO_ROOT / "config" / "profile.yaml"


def load_profile():
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)
