#!/bin/bash
curl -L -o ~/pexscripts/confhistory.py https://www.dropbox.com/sh/t133qp94yu4ef78/AABs4o4YUGzfGLqJ7JRKvYB3a/confhistory.py?dl=0
curl -L -o ~/pexscripts/connectivity.py https://www.dropbox.com/sh/t133qp94yu4ef78/AAAqgTq05ddst_l1ojhQnoTUa/connectivity.py?dl=0
curl -L -o ~/pexscripts/dbsummary.py https://www.dropbox.com/sh/t133qp94yu4ef78/AAAop9ICNcjhqeNugj49ch5ia/dbsummary.py?dl=0
curl -L -o ~/pexscripts/logreader.py https://www.dropbox.com/sh/t133qp94yu4ef78/AADVN0JwwKWK9Xx1zyebzf8Oa/logreader.py?dl=0

# first time setup
if [ ! -f ~/pexscripts/.sync_pexscripts ]; then
    curl -L -o ~/pexscripts/pexsnap.py https://www.dropbox.com/sh/hgy7mvrebwply64/AACYptIUZT164S79DpzdOtWpa/pexsnap.py?dl=0
    echo 'Creating symlinks'
    ln -sf ~/pexscripts/confhistory.py /usr/local/bin/confhistory.py
    ln -sf ~/pexscripts/connectivity.py /usr/local/bin/connectivity.py
    ln -sf ~/pexscripts/dbsummary.py /usr/local/bin/dbsummary.py
    ln -sf ~/pexscripts/logreader.py /usr/local/bin/logreader.py
    ln -sf ~/pexscripts/pexsnap.py /usr/local/bin/pexsnap.py
    echo 'Making scripts executable'
    chmod +x /usr/local/bin/confhistory.py
    chmod +x /usr/local/bin/connectivity.py
    chmod +x /usr/local/bin/dbsummary.py
    chmod +x /usr/local/bin/logreader.py
    chmod +x /usr/local/bin/pexsnap.py
    echo 'Adding run job to cron'
    crontab -l > ~/pexscripts/.cron
    echo "00 10 * * * ~/pexscripts/sync_pexscripts.sh >/dev/null 2>&1" >> ~/pexscripts/.cron
    crontab ~/pexscripts/.cron
    rm -f ~/pexscripts/.cron   
    touch ~/pexscripts/.sync_pexscripts
    echo 'If you see >> crontab: tmp/tmp.xxxxx: Operation not permitted'
    echo 'You need to add your terminal app to the Settings.app "Security & Privacy" > "Full Disk Access"'
    echo '(you can add both `terminal.app` and `iTerm.app`)'
    echo ''
    echo 'Then delete this file ~/pexscripts/.sync_pexscripts and re-run the script'
fi