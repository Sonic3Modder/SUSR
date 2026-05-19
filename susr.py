#!/usr/bin/env python3

import os
import sys
import platform
import time
import threading
import getpass
import pwd
import subprocess
import pam

if platform.system() not in ["Linux", "Darwin"]:
    print("SUSR only works on Linux/macOS")
    sys.exit(1)

p = pam.pam()

# ----------------------------
# STATE (persists during run)
# ----------------------------
attempts = 0
cooldown_active = False
cooldown_lock = threading.Lock()


# ----------------------------
# COOLDOWN TIMER (10 min)
# ----------------------------
def cooldown_timer():
    global cooldown_active
    time.sleep(600)  # 10 min cooldown
    with cooldown_lock:
        cooldown_active = False
    print("\n[susr] cooldown finished — you can try again")


# ----------------------------
# MAIN
# ----------------------------
def main():
    global attempts, cooldown_active

    if len(sys.argv) < 2:
        print("usage: susr <command> [args...]")
        sys.exit(1)

    # block if cooldown is active
    with cooldown_lock:
        if cooldown_active:
            print("[susr] chill — cooldown active, wait 10 min")
            sys.exit(1)

    user = pwd.getpwuid(os.getuid()).pw_name

    password = getpass.getpass(f"[susr] password for {user}: ")

    authenticated = p.authenticate(user, password, service="susr")

    if authenticated:
        attempts = 0
        print("[susr] auth success")
        subprocess.run(sys.argv[1:])
        return

    # ----------------------------
    # FAILED AUTH HANDLING
    # ----------------------------
    attempts += 1
    print("[susr] wrong password")

    if attempts >= 4:
        print("[susr] too many attempts — cooldown started")

        with cooldown_lock:
            cooldown_active = True

        t = threading.Thread(target=cooldown_timer, daemon=True)
        t.start()

        sys.exit(1)


if __name__ == "__main__":
    main()