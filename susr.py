#!/usr/bin/env python3



import os
import sys
import platform
if platform.system() == "Linux" or platform.system() == "Darwin":
    import pwd
    import getpass
    import subprocess
    import pam
    import argparse
    import threading
    import time

    p = pam.pam()
    global attempts
    global timed_attempts
    attempts = 0
    timed_attempts = 0

    def main():
        if len(sys.argv) < 2:
            print("usage: susr <command> [args...]")
            sys.exit(1)

        current_user = pwd.getpwuid(os.getuid()).pw_name

        password = getpass.getpass(f"[susr] password for {current_user}:")

        authenticated = p.authenticate(
            current_user,
            password,
            service="susr"
        )

        def timer():
            time.sleep(600)  # 10 minutes
            global timed_attempts
            timed_attempts += 1
            print("[susr] 10-minute cooldown period completed. You may try again.")

        if not authenticated:
            if not authenticated and attempts < 4:
                print("[susr] Sussy baka, we know your the imposter, we called a emergancy meeting, and the actual admin will deal with this instance, (advice, dont vent infront of others)")
                attempts += 1
            elif not authenticated and attempts >= 4:
                print("[susr] Finally, you got ejected, wait 10 min for next game...")
                # Start background timer
                timer_thread = threading.Thread(target=timer, daemon=True)
                timer_thread.start()
                sys.exit(1)

        command = sys.argv[1:]

        subprocess.run(command)
else:
    print("SUSR is a Linux/Unix Privalge Escalation Tool, and it will not work on Windows (Windows has UAC)")
