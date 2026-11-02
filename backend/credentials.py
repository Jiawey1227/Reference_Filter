"""Store API credentials in the OS credential store, never in project files."""
import keyring

SERVICE = "author-scope-screening"
ACCOUNT = "dashscope-api-key"


def load_key():
    return keyring.get_password(SERVICE, ACCOUNT) or ""


def save_key(value):
    keyring.set_password(SERVICE, ACCOUNT, value)


def clear_key():
    if load_key():
        keyring.delete_password(SERVICE, ACCOUNT)
