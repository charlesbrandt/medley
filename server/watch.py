#!/usr/bin/env python
"""
# Example from watchdog:
# https://github.com/gorakhargosh/watchdog

# Requires watchdog
# pip install watchdog

# Description:
# uses the watchdog library to execute commands after various files change

probably better to use the watchmedo shell utility combined with the tricks.yaml

available tricks are defined here:
https://github.com/gorakhargosh/watchdog/blob/master/src/watchdog/tricks/__init__.py
(not sure where to get others)

ShellCommandTrick should work for most cases

sudo watchmedo tricks tricks.yaml 

#Tried:
- watchdog.tricks.ShellCommandTrick:
    patterns: ["*.py", ]
    shell_command: 'sudo /etc/init.d/medley restart'
#but it did not always restart

"""
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    event_handler = LoggingEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
