# Disable "Line too long"                               pylint: disable=C0301
# Disable "Missing docstring"                           pylint: disable=C0111

from getpass import getpass
import subprocess
import os
import sys

def process(in_file, out_file):
    password = getpass()
    try:
        decrypted = subprocess.call(['openssl', 'aes-256-cbc', '-d', '-out', out_file, '-in', in_file, '-md', 'md5', '-pass', 'pass:{}'.format(password)])
        if decrypted < 0:
            print 'Child was terminated by signal', -decrypted
            sys.exit(2)
        elif decrypted == 1:
            print 'Wrong password'
            sys.exit(2)
        else:
            os.remove(in_file)
    except OSError as e:
        print >>sys.stderr, 'Execution failed:', e
        sys.exit(2)
