"""Windows distribution adapter; application source remains unchanged."""
import argparse
import ctypes
import json
import logging
import os
from pathlib import Path
import socket
import sys
import threading
import time
import urllib.request
import webbrowser


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', action='store_true')
    args = parser.parse_args()
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    home = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'AuthorScopeScreening'
    home.mkdir(parents=True, exist_ok=True)
    os.chdir(home)
    logging.basicConfig(filename=home / 'launcher.log', level=logging.INFO)
    # Keep stdout/stderr valid for print() calls in the windowless executable.
    log = open(home / 'application.log', 'a', encoding='utf-8', buffering=1)
    if sys.stdout is None:
        sys.stdout = log
    if sys.stderr is None:
        sys.stderr = log
    state = home / 'running.json'
    mutex = None
    if sys.platform == 'win32' and not args.smoke_test:
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateMutexW.restype = ctypes.c_void_p
        mutex = kernel.CreateMutexW(None, False, 'Local\\AuthorScopeScreeningLauncher')
        if not mutex:
            raise RuntimeError('Could not create application instance lock')
        if ctypes.get_last_error() == 183:
            for _ in range(40):
                try:
                    url = json.loads(state.read_text())['url']
                    with urllib.request.urlopen(url + '/api/provider', timeout=1):
                        webbrowser.open(url)
                        return
                except Exception:
                    time.sleep(.25)
            ctypes.windll.user32.MessageBoxW(None, 'The app is already starting. Please wait or close its existing window.', 'Author Scope Screening', 0)
            return
    from backend.app import app
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    app.mount('/', StaticFiles(directory=str(root / 'frontend' / 'dist'), html=True), name='ui')
    sock = socket.socket()
    try:
        sock.bind(('127.0.0.1', 8765))
    except OSError:
        sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_config=None))
    worker = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    worker.start()
    try:
        for _ in range(200):
            if server.started:
                break
            if not worker.is_alive():
                raise RuntimeError('Local service failed to start')
            time.sleep(.1)
        else:
            raise RuntimeError('Local service startup timed out')
        state.write_text(json.dumps({'url': url}))
        if args.smoke_test:
            for route in ('/', '/api/provider'):
                with urllib.request.urlopen(url + route, timeout=10) as response:
                    assert response.status == 200
            # Confirm that the packaged credential backend is discoverable.
            import keyring
            assert keyring.get_keyring().priority > 0
            (home / 'smoke-test-ok.txt').write_text('OK')
            return
        import tkinter as tk
        from tkinter import messagebox
        window = tk.Tk()
        window.title('Author Scope Screening')
        window.geometry('460x220')
        tk.Label(window, text='Author Scope Screening', font=('Segoe UI', 16, 'bold')).pack(pady=15)
        tk.Label(window, text='The app is running locally. Keep this window open.').pack()
        tk.Label(window, text=url).pack(pady=5)
        tk.Button(window, text='Open Application', command=lambda: webbrowser.open(url)).pack(pady=8)
        def close():
            from backend.jobs import job_manager, ACTIVE_STATUSES
            if any(job.status in ACTIVE_STATUSES for job in job_manager.jobs.values()):
                if not messagebox.askyesno('Task in progress', 'A task is running. Exit and interrupt it?'):
                    return
            window.destroy()
        tk.Button(window, text='Exit Application', command=close).pack()
        window.protocol('WM_DELETE_WINDOW', close)
        webbrowser.open(url)
        window.mainloop()
    finally:
        server.should_exit = True
        worker.join(timeout=5)
        sock.close()
        state.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        logging.exception('Launcher failed')
        if sys.platform == 'win32' and '--smoke-test' not in sys.argv:
            ctypes.windll.user32.MessageBoxW(None, 'The app could not start. See %LOCALAPPDATA%\\AuthorScopeScreening\\launcher.log.\n' + str(exc), 'Startup error', 16)
        raise
