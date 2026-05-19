#!/bin/bash

echo "Checking if running as root (includes using elevation tools as well)..."
if [ "$(id -u)" -ne 0 ]; then
  echo "Please run this script with sudo or as root."
  exit 1
fi

echo "Editing the susr pam file to use a diffrent conf..."

cat << 'EOF' > /etc/pam.d/susr
#%PAM-1.0

auth       required   pam_unix.so

account    required   pam_access.so

session    required   pam_unix.so
EOF

echo "Making a basic access.conf..."
cat << 'EOF' > /etc/security/access.conf
# --- allow root
+:root:ALL

# --- allow admin group
+:(susr-admin):ALL

# --- allow single user
+:user:ALL

# --- deny everything else
-:ALL:ALL
EOF

# --------------------------------------------------------
# NEW: PYTHON ELEVATION SANDBOX CREATION
# --------------------------------------------------------
echo "Creating dedicated Python interpreter sandbox for susr..."
# Find the real system path of the current python3 installation
REAL_PYTHON=$(readlink -f "$(which python3)")

# Make a dedicated binary clone specifically for your elevator script
cp "$REAL_PYTHON" /usr/bin/python3-susr

echo "Granting process capability overrides to sandbox binary..."
# Assign native process-id manipulation flags to the interpreter sandbox binary
setcap cap_setuid,cap_setgid+ep /usr/bin/python3-susr


echo "Done!, Use the GUI or manually edit it to add users and groups to the access.conf file."
