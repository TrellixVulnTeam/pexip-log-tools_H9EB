#!/usr/bin/env zsh
# 
# Pexip Log Tools for OSX
# Updated for Catalina / Jan 2020
# Updated for Big Sur / Jan 2021
#
# https://docs.pexip.com/admin/log_tools.htm
# 
# Run; zsh -c "$(curl -sSL https://dl.pexip.com/resources/tools/sync_pexscripts.sh)"
#
# Ask for the admin password upfront.
sudo -v

# Create local storage directory & download Pexip scripts.
# Set Pexip script array
declare -a arr=("confhistory.py" "connectivity.py" "dbsummary.py" "logreader.py" "pexsnap.py" "mjxsummary.py" "staticroutes.py" "sync_pexscripts.sh")

# Create local directory
if [[ ! -e ~/pexscripts ]]; then
    mkdir ~/pexscripts
fi

# Backup previous versions of scripts in the array
for i in "${arr[@]}"
do
    if [ -f ~/pexscripts/$i ]; then
        cp ~/pexscripts/$i ~/pexscripts/$i.old
        sudo chown $USER ~/pexscripts/$i.old
    fi
done

# Download scripts
echo 'Downloading Pexip py3 scripts...'
curl --silent -L -o ~/pexscripts/confhistory.py https://www.dropbox.com/sh/t133qp94yu4ef78/AAAnxwZDhbgcFKB-yiz8bTLva/python3/confhistory.py\?dl=0
curl --silent -L -o ~/pexscripts/connectivity.py https://www.dropbox.com/sh/t133qp94yu4ef78/AABTblfnm16CNlkud-89hi2Ja/python3/connectivity.py\?dl=0
curl --silent -L -o ~/pexscripts/dbsummary.py https://www.dropbox.com/sh/t133qp94yu4ef78/AAC6OASTzwdia9cISqMoqqfxa/python3/dbsummary.py\?dl=0
curl --silent -L -o ~/pexscripts/logreader.py https://www.dropbox.com/sh/t133qp94yu4ef78/AAAV3IVLxG41dZEWS44HoixPa/python3/logreader.py\?dl=0
curl --silent -L -o ~/pexscripts/mjxsummary.py https://dl.pexip.com/resources/tools/python3/mjxsummary.py
curl --silent -L -o ~/pexscripts/staticroutes.py https://dl.pexip.com/resources/tools/python3/staticroutes.py
curl --silent -L -o ~/pexscripts/pexsnap.py https://dl.pexip.com/resources/tools/python3/pexsnap.py
curl --silent -L -o ~/pexscripts/sync_pexscripts.sh https://dl.pexip.com/resources/tools/sync_pexscripts.sh

# First time setup
if [ ! -f ~/pexscripts/.sync_pexscripts_v3 ]; then

    if [ -f ~/pexscripts/.sync_pexscripts ]; then
        rm -f ~/pexscripts/.sync_pexscripts
    fi
    # Create run folder, symbolic links and make them executable
    echo 'Creating links & making scripts executable...'
    if [[ ! -e /usr/local/bin ]]; then
        sudo mkdir /usr/local/bin
    fi
    for i in "${arr[@]}"
    do
        # If file exsits don't remove previous py2 symlinks
        if [ ! -f ~/pexscripts/.sync_pexscripts_v3 ]; then
            rm -f /usr/local/bin/$i
        fi
        sudo ln -sf ~/pexscripts/$i /usr/local/bin/${i%.py}
        sudo chmod +x ~/pexscripts/$i && sudo chown -R $USER /usr/local/bin/${i%.py}
    done

    # Add script update to cron
    echo 'Adding run job to cron...'
    crontab -l | grep -v 'sync_pexscripts.sh' > ~/pexscripts/.cron
    echo "00 10 * * * ~/pexscripts/sync_pexscripts.sh >/dev/null 2>&1" >> ~/pexscripts/.cron
    crontab ~/pexscripts/.cron
    rm -f ~/pexscripts/.cron && touch ~/pexscripts/.sync_pexscripts_v3

    # Check for Homebrew & install if we don't have it
    if [[ $(which -s brew) == "brew not found" ]] ; then
        echo "Installing homebrew..."
        ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    fi

    # Check for Sublime Text & install if we don't have it
    if [[ $(which -s subl) == "subl not found" ]] ; then
        # Make sure we’re using the latest Homebrew & Upgrade any already-installed formulae.
        brew update && brew upgrade
        echo 'Installing Sublime Text...'
        brew install --appdir="/Applications" sublime-text
        curl --silent -L -o ~/pexscripts/pex-supportlog.tmLanguage https://www.dropbox.com/s/lczo05e2ti10dme/pex-supportlog.tmLanguage\?dl=1
        sudo mkdir -p ~/Library/Application\ Support/Sublime\ Text\ 3/Packages/User && sudo chown -R $USER ~/Library/Application\ Support/Sublime\ Text\ 3
        sudo ln -sf ~/pexscripts/pex-supportlog.tmLanguage ~/Library/Application\ Support/Sublime\ Text\ 3/Packages/User/pex-supportlog.tmLanguage
    fi

    # Check for pip3 & install if we don't have it so we can install lxml (required for logreader)
    if [[ $(which -s pip3) == "pip3 not found" ]] ; then
        echo 'Installing pip3 & lxml...'
        curl https://bootstrap.pypa.io/get-pip.py -o ~/pexscripts/get-pip.py
        python3 ~/pexscripts/get-pip.py
    fi
    python3 -m pip install --upgrade --user pip
    python3 -m pip install --user lxml
    python3 -m pip install --user alive-progress
fi

# Set permissions
if [[ ! $EUID -ne 0 ]]; then
    chown -R $SUDO_USER ~/pexscripts && chmod 700 ~/pexscripts
else
    chown -R $USER ~/pexscripts && chmod 700 ~/pexscripts
fi
echo 'Done'

# Rehash the shell
sleep 2 && exec zsh && rehash