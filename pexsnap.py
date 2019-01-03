#!/usr/bin/env python
# pexsnap: process Pexip snapshots.
#
# usage: pexsnap.py [-h] [-i IN] [-o OUT]
#
# optional arguments:
#   -h, --help              show this help message and exit
#   -i IN, --input IN       path containing the snapshot(s)
#   -o OUT, --output OUT    path to extract the snapshot
#
# Disable "Invalid constant name"                       pylint: disable=C0103
# Disable "Line too long"                               pylint: disable=C0301
# Disable "Too many lines in module"                    pylint: disable=C0302
# Disable "Missing docstring"                           pylint: disable=C0111
# Disable "Too many branches"                           pylint: disable=R0912
# Disable "Too many statements"                         pylint: disable=R0915
# Disable "Unnecessary parens"                          pylint: disable=C0325
# Disable "Wrong Import Position"                       pylint: disable=C0413

import argparse
import fileinput
import glob
import os
from os.path import isfile, join
from os.path import expanduser
import re
import subprocess
import sys
sys.path.append(expanduser('~/pexscripts'))
import tarfile
from datetime import datetime
libavailable = 1
try:
    import pexsnaplib as pxl
except ImportError:
    libavailable = 0

# Enable "Wrong Import Position"                       pylint: enable=C0413
#
# config
open_in_atom = False # open parsed files in Atom when script completes
open_in_subl = False # open parsed files in Sublime Text when script completes

check_for_dnsfail_events = True # check for dns failures
check_for_adapter_events = True # check for adapter failures
check_for_irpulse_events = True # check for irregular pulse events
check_for_ir_ping_events = True # check for irregular ping events
check_for_martian_events = True # check for possible duplicate IP addresses
check_for_sipspam_events = True # check for SIP spam events
check_for_reactor_events = True # check for reactor stalling events
check_for_vmotion_events = False # check for vmotion events. (internal use, leave False)
check_for_connect_events = True # check for connectivity events
check_for_exchang_events = False # check for ews events (external script not complete, leave False)

# Extract snapshot to pre-defined directory (below) if True (~/Downloads/snapshots/)
# -o argument only takes folder name if True i.e. '-o monday_snapshot'
extract_snapshot_to_dir = False
parsed_snaps = expanduser('~/Downloads/snapshots')

measure = False # measure execution time in sec

# setup variables
develop = 'unified_developer.log'
support = 'unified_support.log'
usyslog = 'unified_syslog.log'
nsreport = 'pex_report_dns_failures.log'
dbreport = 'pex_report_dbreport.log'
lrreport = 'pex_report_logreader.log'
vmreport = 'pex_health_vmotionreport.log'
cnreport = 'pex_health_connectivity_report.log'
exreport = 'pex_report_scheduling.log'
irregularpulsetext = 'pex_health_irregular_pulse.log'
irregularpingstext = 'pex_health_irregular_ping.log'
rectorstallingtext = 'pex_health_reactor_stalling.log'
e1adapteresetstext = 'pex_health_adapter_resets.log'
martiansourcestext = 'pex_health_martian_sources.log'

actuallogdir = '/var/log/'
parsedlogdir = '/var/log/parsed/'
logr_path = '/usr/local/bin/logreader.py'
dbsu_path = '/usr/local/bin/dbsummary.py'
vmot_path = '/usr/local/bin/vmotion.py'
conn_path = '/usr/local/bin/connectivity.py'
exch_path = '/usr/local/bin/scheduling.py'

atom_path = '/Applications/Atom.app/Contents/MacOS/Atom'
subl_path = '/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl'

suspect_uas = re.compile(r'(\bDetail=\"\^MINVITE\b.+User-Agent: (Asterisk PBX|CSipSimple|custom|friendly-request|friendly-scanner|iWar|Gulp|pplsip|siparmyknife|sipcli|sipptk|sipsak|sipsscuser|sipv|sipvicious|sip-scan|SIVuS|smap|sundayddr|Test Agent|UsaAirport|VaxIPUserAgent|VaxSIPUserAgent))')

sep = '--------------------------------------------------'

sip_spam = 0
# start

def parse_args(args=None):
    parser = argparse.ArgumentParser(description='Python variant of the Pexip Log Tools')
    parser.add_argument('-i', '--input', help='path containing the snapshot(s)')
    parser.add_argument('-o', '--output', help='path to extract the snapshot')
    return parser.parse_args(args=args)

def get_ordered_list_of_snaps(snapshot_path):
    ordered_snaps = {}
    order_id = 0
    num_files = -1
    found = 0
    for file_name in os.listdir(snapshot_path):
        if isfile(join(snapshot_path, file_name)):
            if file_name.startswith('diagnostic_snapshot_'):
                found = 1
                size = str(os.stat(snapshot_path + '/' + file_name).st_size / 1048576)
                ordered_snaps[order_id] = os.path.join(snapshot_path, file_name), size
                if order_id > num_files:
                    num_files = order_id
                    order_id += 1
    if not found:
        return ()
    return (ordered_snaps, num_files)

def select_snap(snapshot_path):
    snaps = get_ordered_list_of_snaps(snapshot_path)
    if not snaps:
        print ('No snapshots found in {}'.format(snapshot_path))
        print ('{}'.format(sep))
        sys.exit(2)
    else:
        if len(snaps[0].items()) == 1:
            for key, value in snaps[0].iteritems(): # return the only snapshot found
                return value[0]
        snap_count = 0
        print ('{}'.format(sep))
        print ('Number\tSize\tFilename')
        for a, b in snaps[0].itervalues():
            print ('{}\t{}MB\t{}'.format(snap_count, b, os.path.split(a)[1]))
            snap_count += 1
        print ('{}'.format(sep))
        snap_count -= 1
        try:
            snap_select = int(raw_input('Select a number: '))
            while snap_select < 0 or snap_select > snaps[1]:
                print('Not an appropriate choice.')
                snap_select = int(raw_input('Select a number: '))
        except ValueError:
            print('That\'s not an option!')
            sys.exit(2)
        for key, value in snaps[0].iteritems(): # return selected snapshot
            if key == snap_select:
                return value[0]

def extract_snap(folder, chosen_one): # extract snapshot
    if not os.path.exists(folder):
        os.makedirs(folder)
    if libavailable == 1:
        try:
            with tarfile.open(chosen_one) as tar:
                canopen = True
        except:
            canopen = False
        if not canopen:
            try:
                pxl.process(chosen_one, (folder + '/' + os.path.split(chosen_one)[1].replace(".tgz", "-processed.tgz")))
            except:
                print 'An error occurred'
                sys.exit(1)
            chosen_one = (folder + '/' + os.path.split(chosen_one)[1].replace(".tgz", "-processed.tgz"))
    try:
        with tarfile.open(chosen_one) as tar:
            print ('Extracting {} to {}'.format(chosen_one.split('/')[-1], folder))
            tar.extractall(path=folder)
            os.rename(chosen_one, (folder + '/' + os.path.split(chosen_one)[1]))
    except:
        print 'Unable to extract file, the file is either corrupt or encrypted.'
        sys.exit(1)
    return folder

def events(psnapdir):
    global sip_spam

    if not os.path.exists(psnapdir + parsedlogdir): # create parsed log directory
        os.makedirs(psnapdir + parsedlogdir)

    dev_files_array = sorted(glob.glob(os.path.join(psnapdir, 'var/log/unified_developer.log*')), key=os.path.getmtime, reverse=True)
    sup_files_array = sorted(glob.glob(os.path.join(psnapdir, 'var/log/unified_support.log*')), key=os.path.getmtime, reverse=True)
    sys_files_array = sorted(glob.glob(os.path.join(psnapdir, 'var/log/unified_syslog.log*')), key=os.path.getmtime, reverse=True)

    print ('Checking for known events in the logs files')

    for line in fileinput.input(dev_files_array):
        if check_for_ir_ping_events:
            matchip = re.compile(r'Irregular ping detected.+\(\d[1-9]+\.\d[0-9].+sec\)')
            if matchip.findall(line):
                with open(psnapdir + parsedlogdir + irregularpingstext, 'ab') as output_file:
                    output_file.write(("{}:{}").format(fileinput.filename().split('/')[-1], line))
        if check_for_ir_ping_events:
            if 'Reactor stalling' in line:
                with open(psnapdir + parsedlogdir + rectorstallingtext, 'ab') as output_file:
                    output_file.write(("{}:{}").format(fileinput.filename().split('/')[-1], line))

    for line in fileinput.input(sup_files_array):
        if check_for_irpulse_events:
            if 'Irregular pulse duration detected' in line:
                with open(psnapdir + parsedlogdir + irregularpulsetext, 'ab') as output_file:
                    output_file.write(("{}:{}").format(fileinput.filename().split('/')[-1], line))
        if check_for_dnsfail_events:
            match = re.compile(r'Name=\"support\.dns\"(?:(?!\bAAAA\b).)*?Result=\"\"')
            if match.findall(line):
                with open(psnapdir + parsedlogdir + nsreport, 'ab') as output_file:
                    output_file.write(("{}:{}").format(fileinput.filename().split('/')[-1], line))

        # parse support log for sip spam
        if check_for_sipspam_events:
            if suspect_uas.findall(line):
                sip_spam += 1

    for line in fileinput.input(sys_files_array):
        if check_for_adapter_events:
            match = re.compile(r'e1000.*Reset adapter')
            if match.findall(line):
                with open(psnapdir + parsedlogdir + e1adapteresetstext, 'ab') as output_file:
                    output_file.write(("{}:{}").format(fileinput.filename().split('/')[-1], line))
        if check_for_martian_events:
            match = re.compile(r'IPv4: martian source \d{1,3}.\d{1,3}.\d{1,3}.\d{1,3} from \d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}, on dev eth\d{1}') # potential IP conflict
            if match.findall(line):
                lline = line.split(' ')
                src = lline[7]
                dst = lline[9].strip(',')
                if src == dst:
                    with open(psnapdir + parsedlogdir + martiansourcestext, 'ab') as output_file:
                        output_file.write(("{}:{}").format(fileinput.filename().split('/')[-1], line))

def run_lr(path, newpath):
    try:
        subprocess.Popen(("{} {}* > {}").format(logr_path, path, (newpath + parsedlogdir + lrreport)), shell=True).wait()
    except subprocess.CalledProcessError as e:
        print e.output


def run_script(path, script, output):
    try:
        subprocess.Popen(("{} {} > {}").format(script, path, (path + parsedlogdir + output)), shell=True).wait()
    except subprocess.CalledProcessError as e:
        print e.output

# run
def main():
    if measure:
        start = datetime.now()
    cwd = os.getcwd()
    args = parse_args()
    if not args.input:
        chosen_one = select_snap(cwd) # select a snapshot
    else:
        chosen_one = select_snap(args.input)
    if not args.output:
        if extract_snapshot_to_dir:
            folder = parsed_snaps + "/" + chosen_one.replace(".tgz", "").split('/')[-1]
        else:
            folder = chosen_one.replace(".tgz", "")
    else:
        if extract_snapshot_to_dir:
            folder = parsed_snaps + "/" + args.output
        else:
            folder = args.output
    try:
        newdir = extract_snap(folder, chosen_one) # extract snapshot to folder
        events(newdir) # parse logs for known events
        if check_for_adapter_events:
            if os.path.isfile(newdir + parsedlogdir + e1adapteresetstext) and os.stat(newdir + parsedlogdir + e1adapteresetstext).st_size != 0:
                print ('-> Adapter resets detected, see {}{}{} ({}KB)'.format(newdir, parsedlogdir, e1adapteresetstext, str(os.stat(newdir + parsedlogdir + e1adapteresetstext).st_size / 1024)))
        if check_for_dnsfail_events:
            if os.path.isfile(newdir + parsedlogdir + nsreport) and os.stat(newdir + parsedlogdir + nsreport).st_size != 0:
                print ('-> DNS failures detected, see {}{}{} ({}KB)'.format(newdir, parsedlogdir, nsreport, str(os.stat(newdir + parsedlogdir + nsreport).st_size / 1024)))
        if check_for_ir_ping_events:
            if os.path.isfile(newdir + parsedlogdir + irregularpingstext) and os.stat(newdir + parsedlogdir + irregularpingstext).st_size != 0:
                print ('-> Irregular pings detected, see {}{}{} ({}KB)'.format(newdir, parsedlogdir, irregularpingstext, str(os.stat(newdir + parsedlogdir + irregularpingstext).st_size / 1024)))
        if check_for_reactor_events:
            if os.path.isfile(newdir + parsedlogdir + irregularpulsetext) and os.stat(newdir + parsedlogdir + irregularpulsetext).st_size != 0:
                print ('-> Irregular pulse durations detected, see {}{}{} ({}KB)'.format(newdir, parsedlogdir, irregularpulsetext, str(os.stat(newdir + parsedlogdir + irregularpulsetext).st_size / 1024)))
        if check_for_martian_events:
            if os.path.isfile(newdir + parsedlogdir + martiansourcestext) and os.stat(newdir + parsedlogdir + martiansourcestext).st_size != 0:
                print ('-> Possible duplicate IPv4 addresses detected, see {}{}{} ({}KB)'.format(newdir, parsedlogdir, martiansourcestext, str(os.stat(newdir + parsedlogdir + martiansourcestext).st_size / 1024)))
        if check_for_sipspam_events:
            if sip_spam != 0:
                print ('-> SIP INVITEs detected from suspect user agents: {} events'.format(sip_spam))
        if check_for_irpulse_events:
            if os.path.isfile(newdir + parsedlogdir + rectorstallingtext) and os.stat(newdir + parsedlogdir + rectorstallingtext).st_size != 0:
                print ('-> Reactor stalls detected, see {}{}{} ({}KB)'.format(newdir, parsedlogdir, rectorstallingtext, str(os.stat(newdir + parsedlogdir + rectorstallingtext).st_size / 1024)))
        if os.path.isfile(logr_path):
            print ('Running logs through logreader')
            run_lr((newdir + actuallogdir + support), newdir) # run LogReader report on current log files and pipe the result out to a text file
        else:
            print ('logreader not found, skipping..')
        if os.path.isfile(dbsu_path):
            print ('Running database through dbsummary')
            run_script(newdir, dbsu_path, dbreport) # run dbsummary report on current database and pipe the result out to a text file
        else:
            print ('dbsummary not found, skipping..')
        if check_for_vmotion_events:
            if os.path.isfile(vmot_path):
                print ('Checking for vmotion events')
                run_script(newdir, vmot_path, vmreport) # run vmotion report on current log files and pipe the result out to a text file
        if check_for_connect_events:
            if os.path.isfile(conn_path):
                print ('Checking for connectivity events')
                run_script(newdir, conn_path, cnreport) # run connectivity report on current database and pipe the result out to a text file
        if check_for_exchang_events:
            if os.path.isfile(exch_path):
                print ('Checking for exchange events')
                run_script(newdir, exch_path, exreport) # run exchange report on current log files and pipe the result out to a text file
        print ('{}'.format(sep))
        print ('Done, you can find the parsed log files in {}'.format(newdir + parsedlogdir))
        print ('{}'.format(sep))
        if open_in_atom:
            subprocess.Popen([atom_path, newdir])
        if open_in_subl:
            subprocess.Popen([subl_path, newdir])
        if measure:
            end = datetime.now()
            print('Duration: {}'.format(end - start))

    except OSError as err:
        print err
        sys.exit(2)

if __name__ == "__main__":
    try:
        main()
    except (IOError, KeyboardInterrupt):
        pass
