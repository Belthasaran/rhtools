# Purpose of this Program
This program facilitates Downloading and running SMW Romhacks.

This is a sample release.
This program is incomplete and a work in progress.

# Running the program
   This program requires Python 3.10.x.
   The program is written to run on Linux, or Windows Subsystem for Linux
   *  Please install the pre-requisites Including: Flips, Asar,
      and a Legally-acquired original SMW rom as discussed in the Section Pre-requisites.

 After installing the pre-requisites:
    You can run the GUI by launching gui.py
      python3 gui.py

    Currently the GUI only supports listing all Hacks in
    the database and choosing a hack.   

    The "Play this hack" button - Automatically applies the
    patch to the vanilla SMW game and Launches the patched
    file (If successful)

    You can search for Romhacks in the database from the command line:
      python3 search.py kaizo

    (Currently the database only contains a limited selection)

    You can automatically download, patch, and ready a hack to run
    by launching pb_repatch.py
       for example, to download and Patch Hack number 11374,
       DRAM World: 
      # python3 pb_repatch.py 11374

    You can send a ROM to the emulated or real  SNES by running pb_sendtosnes.py
      # python3 pb_sendtosnes.py rom/blah.sfc

       This requires an Emulator be installed Or  Usb2snes AND
       The QUSB2SNES  sendtosd2snes.exe tool.

      This requires Editing the llaunch_rand.sh  script
      according to your local Needs.

# Prerequisites

Requires PYTHON3

## Base ROM

This program requires a legally-acquired base rom to use.
This file should be vanilla SMW.

Name the file smw.sfc  and Place the file in the same folder you
run the program from

## FLIPS and ASAR

- You need the floating IPS Patcher flips And ASAR 1.71 installed.

- Those products are both under the GNU GPL.  For your convenience: This website contains
a copy of them:  Download  flips-rhtool-0.1_2023.tar.gz

If you are a Windows Subsystem for Linux user,  then just use 7-zip to extract the file and its subfolders in C:\SNESGAMING

Linux users can extract the archive and then copy  bin/flips and bin/asar   To  /usr/local/bin.
  tar zxvf flips-rhtool-0.1_2023.tar.gz
  sudo cp bin/flips /usr/local/bin
  sudo cp bin/asar /usr/local/bin

## Linux

This program is written on Linux to run on Linux.

The following steps are for Windows users.

Windows users should still be able to run this program:
    * First: install Windows Subsystem for Linux (see below for details)
    * Next: download and install MobaXterm

## Setup for Windows Users

Windows users: Please create a directory named C:\SNESGAMING
and put these scripts in a folder named RHTOOLS below C:\SNESGAMING

When you install ASAR and FLIPS as required,  create a
folder called C:\SNESGAMING\bin   then copy The linux versions of
asar and flips to that bin folder.

## Windows Subsystem for Linux

I recommend the following article:
https://ubuntu.com/tutorials/install-ubuntu-on-wsl2-on-windows-10#1-overview

In short - the first steps are:
wsl --set-default-version 2
wsl install -d ubuntu

After you have installed your environment,  Launch  MobaXterm, 
choose "Start Local Terminal" and double click the WSL-Ubuntu user Session.

If there is no WSL-Ubuntu User session, then  Right click "User Sessions",
pick "New Session",  then Choose WSL on the far Right, and
change Distribution to "Ubuntu",  then click OK.

Open a  Ubuntu-WSL Tab

then

cd /mnt/c/snesgaming/rhtools
python3 gui.py


## PIP Modules:
   Please install PIP modules   before running 

pip3 install -r requirements.txt

Please install
pip3 install ipfshttpclient
pip3 install cryptography
pip3 install requests
pip3 install compress




