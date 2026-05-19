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
+:barrett:ALL

# --- deny everything else
-:ALL:ALL
EOF

echo "Done!, Use the GUI or manually edit it to add users and groups to the access.conf file."
