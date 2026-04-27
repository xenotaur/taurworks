# taurworks
A suite of Unix utilities used by the Centaur in his day-to-day work.

## Installation

NOTE: Check your .bashrc and .bash_profile prior to overwriting them,
as your local installation may have placed things in these files.

There are two ways of installing this: dead source and live source.

* Dead Source: Copy the bin directory to ~/bin on a Linux installation,
  and copy the following files to the root directory:

  * cd ~
  * cp ~/bin/dot.bash_profile .bash_profile
  * cp ~/bin/dot.bashrc .bashrc
  * cp -r ~/bin/byobu .byobu
  
  This will be disconnected from source control, but it's the simplest.

* Live Source: Place taurworks someplace safe and symbolically link
  the files so that the connections are live:

  * cd ~
  * ln -s taurworks/bin ~/bin
  * ln -s ~/bin/dot.bash_profile .bash_profile
  * ln -s ~/bin/dot.bashrc .bashrc
  * ln -s ~/bin/byobu .byobu

  This will enable you to track changes and upload them via `git push`.

## Documentation

### The Bin Directory

Commands and Aliases
* grr
* cpd
* drq
* grj
* today
* xi
* aquamacs
* sample.py
* logscript
* psg
* grr ->retire

To rework
* sample.py

To retire

* Blog Image tools
  * imagelink
  * fileimages.py
* parallels.original.bashrc

### Screen Tools
* byobu
* screen
  * myscreen
  * screenrc

### AWS Tools
  * extract-instance-name
  * aws-setup-check
  * awsh
  * awst

### The Prompt


### The Command Logger
* lastcommand
* logged
* group_logged.py


## CI Validation

This repository separates fast pull-request validation from smoke validation.

- Fast CI (`.github/workflows/ci.yml`) runs on pull requests and pushes to `main`:
  - `scripts/test`
  - `scripts/lint`
  - `scripts/format --check`
- Smoke CI (`.github/workflows/smoke.yml`) runs as an explicit confidence check via:
  - manual dispatch (`workflow_dispatch`)
  - published releases
  - a weekly schedule

Smoke CI runs `scripts/smoke` and is intentionally isolated from normal PR feedback.
