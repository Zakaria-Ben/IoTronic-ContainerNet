#!/usr/bin/python

import os

def function():
     cmd = 'echo "$(ls | grep 5)"'
     return os.system(cmd)


#cmd = 'result="$(ls | grep 5)"'
#os.system(cmd)
os.system('sed -i "s|listen 50000 default_server;|listen "$(ls | grep 5)" 
default_server;|g" /etc/nginx/sites-available/default')
os.system('sed -i "s|50000 default_server;|"$(ls | grep 5)" 
default_server;|g" /etc/nginx/sites-available/default')
os.system('sed -i "s|<REGISTRATION-TOKEN>|"$HOSTNAME$(ls | grep 5)"|g" 
/etc/iotronic/settings.json')
#replace 0.0.0.0 by the IP address of the WAMP agent
os.system('sed -i "s|<WAMP-SERVER>:<WAMP-PORT>|"0.0.0.0:8181"|g" 
/etc/iotronic/settings.json')
os.system('sed -i "s|<IOTRONIC-REALM>|"s4t"|g" 
/etc/iotronic/settings.json')
