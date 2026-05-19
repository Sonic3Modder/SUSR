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

# Ensure the script starts with access to root permissions
if os.getuid() != 0 and os.geteuid() != 0:
    print("[susr] critical error: this script must be run with root capabilities to elevate.")
    print("       See deployment instructions below.")
    sys.exit(1)

# Save root's ID, then drop current effective permissions down to the calling user
# This ensures PAM doesn't automatically bypass authentication because we're 'root'
real_uid = int(os.environ.get("SUDO_UID", os.getuid()))
if real_uid == 0:
    # If invoked directly as root, find who called it via logname or fallback
    try:
        real_uid = pwd.getpwnam(os.getlogin()).pw_uid
    except Exception:
        real_uid = int(os.getuid())

# Drop to the real user for the prompt and PAM authentication
os.setegid(pwd.getpwuid(real_uid).pw_gid)
os.seteuid(real_uid)

p = pam.pam()
attempts = 0
cooldown_active = False
cooldown_lock = threading.Lock()

def cooldown_timer():
    global cooldown_active
    time.sleep(600)
    with cooldown_lock:
        cooldown_active = False
    print("\n[susr] cooldown finished — you can try again")

def authenticate(user, password):
    result = p.authenticate(user, password, service="susr")
    if result:
        return True, "Success"
    reason = getattr(p, 'reason', 'Authentication failed')
    return False, reason

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

    ok, reason = authenticate(user, password)

    # ----------------------------
    # SUCCESS
    # ----------------------------
    if ok:
        with cooldown_lock:
            attempts = 0
        print("[susr] auth success")
        
        # ELEVATION: Restore full root privileges permanently for the sub-process
        try:
            os.setuid(0)
            os.setgid(0)
        except PermissionError:
            print("[susr] critical error: failed to restore root privileges.")
            sys.exit(1)
            
        # Run the command with root environment defaults
        env = os.environ.copy()
        env["USER"] = "root"
        env["HOME"] = "/root"
        
        subprocess.run(sys.argv[1:], env=env)
        return

    # ----------------------------
    # FAILURE
    # ----------------------------
    with cooldown_lock:
        attempts += 1
        current_attempts = attempts

    print("[susr] access denied")
    print(f"[susr] reason: {reason}")

    if current_attempts >= 4:
        with cooldown_lock:
            cooldown_active = True
        print("[susr] too many failures — cooldown triggered")
        threading.Thread(target=cooldown_timer, daemon=True).start()
    else:
        print(f"[susr] attempt {current_attempts}/4")

if __name__ == "__main__":
    main()
