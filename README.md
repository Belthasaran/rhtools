# Purpose of this Program
This program facilitates Downloading and running SMW Romhacks.

This is a sample release.
This program is incomplete and a work in progress.

# Running the program
   This program requires Python 3.10.x.
   The program is written to run on Linux, or Windows Subsystem for Linux
   *  Please install the pre-requisites Including: Flips, Asar,
      and a Legally-acquired original SMW rom as discussed in the Section Pre-requisites.

 Download
    Download FLIPS and  the Program from
      https://github.com/Belthasaran/rhtools/releases

      For Windows users, I recommend extracting all 3 files in C:\SNESGAMING
      rhtools-0.2.tar.gz
      rhtools-sampledata-202308.tar.gz
      flips-rhtool-0.1_2023.tar.gz
      


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


## Database Maintenance


PROCEDURE TO ADD A HACK TO THE DATABASE:


To add hack with ID example1234

1. Create folders  zips/ hacks/

2.   create  hacks/example1234
     This should be a text file in JSON format.

The JSON file should contain Information which identifies the hack..

You will need to either prepare this manually or by other means:

{
    "added": "2023-09-03",
    "author": "test",
    "authors": "test",
    "demo": "No",
    "description": "test",
    "id": "example1234",
    "length": "unknown",
    "name": "example hack",
    "rating": [
        "0.0"
    ],
    "tags": [
        "traditional"
    ],
    "tags_href": "",
    "type": "Standard: Normal",
    "url": "https://example.com/info/smw_example",
    "name_href": "//dl.example.com/download/smw_example.zip",
    "author_href": "/?p=profile&id=example"
}


3.  Create   zips/example1234.zip

The .zip file should contain  example1234.bps   with the Patch data.
the Patch must be against the vanilla SMW game in BPS file format.


4.  Run mkblob
     python3 mkblob.py  example1234

     The program mkblob will Automatically extract the ".zip" file and apply the patch.
     The output looks like:

     $ python3 mkblob.py example

example.bps
The patch was applied successfully!
::: {'added': '2023-09-03', 'author': 'test', 'authors': 'test', 'demo': 'No', 'description': 'test', 'id': 'example', 'length': 'unknown', 'name': 'example hack', 'rating': ['0.0'], 'tags': ['traditional'], 'tags_href': '', 'type': 'Standard: Normal', 'url': 'https://example.com/info/smw_example', 'name_href': '//dl.example.com/download/smw_example.zip', 'author_href': '/?p=profile&id=example', 'patch': 'patch/Rf_sNY6-VeRrbd3ehCVZ8r6qsJcsGOsg', 'pat_sha224': '07886ea9791a671581e7bd2e5bc36999bf9e1598838d5b7f505f173a', 'pat_sha1': '556ada885b72ba0c060d7a569a357501509c2b7a', 'pat_shake_128': 'Rf_sNY6-VeRrbd3ehCVZ8r6qsJcsGOsg', 'result_sha224': 'fdc4c00e09a8e08d395003e9c8a747f45a9e5e94cbfedc508458eb08', 'result_sha1': '6b47bb75d16514b6a476aa0c73a683a2a4c18765', 'result_shake1': '1SNFIbeimj0ck4t5ylWe6a80jqt9gYkL', 'rom': 'rom/example_1SNFIbeimj0ck4t5ylWe6a80jqt9gYkL.sfc', 'patchblob1_name': 'pblob_example_a45829efe5', 'patchblob1_key': 'dGRJUDJWc0txZXA2b2E5a0lxa1dQV2d1c2VQZWZ2aW14SU1MMzJFMWc1ND0=', 'patchblob1_sha224': 'a45829efe55990d404d9136207f9ded73793b9b9e761195baf2e3d31', 'romblob_salt': 'kyjCSqrKdeH3l4_t5gbcbQ==', 'romblob_name': 'rblob_example_f1fc80f5d9'}
rom/example_1SNFIbeimj0ck4t5ylWe6a80jqt9gYkL.sfc


    At this point the  hacks/example  File has Already been updated and is ready to add to the database.



5.      bash do_addhacks.sh
     This script will scan the  hacks/  directory  and attempt to add them to the database.






























