[ -z "$PS1" ] && return

#export PS1="\[\e[31m\]ps1 thing\[\e[m\] \[\e[33m\]\w\[\e[m\] > "
#export TERM=xterm-256color
alias grep="grep --color=auto"
alias ls="ls --color=auto"

echo -e "\e[1;31m"
cat<<EOF
|\  |   /\   |\ |  |   /\   ------    |\ |   |-- |\  | |\  |-- |\\
| \ |  /--\  |/ |--|  /--\     |      |\ |   |-- | \ | | | |-- |/
|  \| /    \ |  |  | /    \    |      |/ |__ |__ |  \| |/  |__ |\\
EOF
echo -e "\e[0;33m"

# Turn off colors
echo -e "\e[0m"
