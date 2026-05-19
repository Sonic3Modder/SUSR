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
# PAM AUTH WRAPPER
# ----------------------------
def authenticate(user, password):
    """
    Authenticates against PAM and extracts precise failure codes.
    Returns: (bool, str)
    """
    result = p.authenticate(
        user,
        password,
        service="susr"
    )
    
    if result:
        return True, "Success"
    
    # Extract the exact reason or error code string from python-pam
    reason = getattr(p, 'reason', 'Authentication failed')
    return False, reason


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

    # Authenticate and capture the true PAM result
    ok, reason = authenticate(user, password)

    # ----------------------------
    # SUCCESS
    # ----------------------------
    if ok:
        with cooldown_lock:
            attempts = 0
        print("[susr] auth success")
        subprocess.run(sys.argv[1:])
        return

    # ----------------------------
    # FAILURE
    # ----------------------------
    with cooldown_lock:
        attempts += 1
        current_attempts = attempts

    print("[susr] access denied")
    print(f"[susr] reason: {reason}")  # Displays the exact PAM feedback

    if current_attempts >= 4:
        with cooldown_lock:
            cooldown_active = True
        print("[susr] too many failures — cooldown triggered")
        threading.Thread(target=cooldown_timer, daemon=True).start()
    else:
        print(f"[susr] attempt {current_attempts}/4")


if __name__ == "__main__":
    main()
