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

attempts = 0
cooldown_active = False
cooldown_lock = threading.Lock()


# ----------------------------
# COOLDOWN TIMER
# ----------------------------
def cooldown_timer():
    global cooldown_active
    time.sleep(600)
    with cooldown_lock:
        cooldown_active = False
    print("\n[susr] cooldown finished — you can try again")


# ----------------------------
# PAM AUTH WRAPPER (NEW)
# ----------------------------
def authenticate(user, password):
    """
    Returns:
    True  -> success
    False -> failure (could be wrong password OR access.conf deny)
    """

    result = p.authenticate(
        user,
        password,
        service="susr"
    )

    return result


# ----------------------------
# MAIN
# ----------------------------
def main():
    global attempts, cooldown_active

    if len(sys.argv) < 2:
        print("usage: susr <command> [args...]")
        sys.exit(1)

    with cooldown_lock:
        if cooldown_active:
            print("[susr] chill — cooldown active, wait 10 min")
            sys.exit(1)

    user = pwd.getpwuid(os.getuid()).pw_name
    password = getpass.getpass(f"[susr] password for {user}: ")

    ok = authenticate(user, password)

    # ----------------------------
    # SUCCESS
    # ----------------------------
    if ok:
        attempts = 0
        print("[susr] auth success")
        subprocess.run(sys.argv[1:])
        return

    # ----------------------------
    # FAILURE (IMPORTANT PART)
    # ----------------------------
    attempts += 1

    # THIS is your new clarity layer
    print("[susr] access denied")

    if attempts == 1:
        print("[susr] reason: wrong password OR not in access.conf")

    elif attempts < 4:
        print(f"[susr] attempt {attempts}/4")

    # ----------------------------
    # COOLDOWN TRIGGER
    # ----------------------------
    if attempts >= 4:
        print("[susr] too many attempts — cooldown started")

        with cooldown_lock:
            cooldown_active = True

        threading.Thread(target=cooldown_timer, daemon=True).start()
        sys.exit(1)


if __name__ == "__main__":
    main()