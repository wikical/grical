#!/bin/bash

# var for session name (to avoid repeated occurences)
sn=gricaldev
BASE="$HOME/grical"

# Start the session and window 0
#   This will also be the default cwd for new windows created
#   via a binding unless overridden with default-path.
cd $BASE

# Create a bunch of windows
tmux new-session -s "$sn" -n 'Django Development Server' -d
tmux new-window -t "$sn:1" -n 'Celery' -d

# Runs the Django Development Server on window 0
tmux send-keys -t "$sn:0" "cd ~/grical; python manage.py runserver 0.0.0.0:8000" C-m

# Runs celery on window 1
tmux send-keys -t "$sn:2" "cd ~/grical; export DJANGO_SETTINGS_MODULE=grical.settings.settings; celery -A grical worker -l info" C-m

# Select window #0 and attach to the session
tmux select-window -t "$sn:0"
tmux -2 attach-session -t "$sn"
