[ -z "$PS1" ] && return

export PS1="\[\e[33m\]\u@\[\e[1;31m\]Blender\[\e[36m\] \w \[\e[33m\]>\[\e[0m\] "
export TERM=xterm-256color
alias grep="grep --color=auto"
alias ls="ls --color=auto"

echo -e "\e[1;31m"
cat<<EOF
|\  |   /\   |\ |  |   /\   -------    |\ |   |-- |\  | |\  |-- |\\
| \ |  /--\  |/ |--|  /--\     |       |\ |   |-- | \ | | | |-- |/
|  \| /    \ |  |  | /    \    |       |/ |__ |__ |  \| |/  |__ |\\
EOF

# Turn off colors
echo -e "\e[0m"
