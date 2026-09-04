This is the fast and slow recipes to get the latest Python 3.14.7, near latest 
numpy 2.4.6, and PyTorch 1.8.1 with full NVIDIA CUDA GPU acceleration working 
under macOS High Sierra. 

The fast notes: In a nutshell hopefully you already have an intel mac with 
NVIDIA hardware running macOS 10.13.6 High Sierra, have installed XCode 10.1 
with the matching command line tools, the NVIDIA graphics drivers, NVIDIA CUDA 
10.1 for macOS, and macports. Then setup the /opt/tools area : “sudo mkdir 
/opt/tools”, “sudo chown $USER:staff /opt/tools”, which by default (in 
0000_env) is where everything gets installed after built, make sure these 
scripts are located in a build area that has around 7GB(!) of scratch build 
space. The /opt/tools area needs only 700MB, /opt/tools/bin should be on your 
path to run and test everything as you go, for details see below, then launch 
the included scripts in this order:

00_xz = installs xz-5.8.3
085_openssl = installs openssl 3.6.4 tools and libraries
0890_python = installs Python 3.14.7 and pip3
0891x_numpy = uses git and installs numpy 2.4.6, patches one file.
0892x_pytorch = uses git and installs pytorch v1.8.1, patches eight files.
pytorch_test = contains a set of basic scripts to check that things are working.

Once everything is working, the build area can be cleaned out as it’s not 
needed anymore.
Updates can be as little as a single line and rebuild, but with numpy and 
pytorch they might already be a the end of their line. If a new version of 
python adds another required patch, I’ll post it here.

Please take notes. I’d love to know if I’m missing something, or if anyone else 
out there is crazy enough to follow this path, or manages to also get it 
working. I’ve been doing this long enough that when things break, I often just 
fix it and move on. 

The slow notes:
This was heavily inspired by the Linux from Scratch Project, and years of 
systems administration experience. If you do something once, you’ll forget it 
quickly. If you script something, you can build and improve on it even years 
later on completely different environments. 

Notes on Apple/NVIDIA hardware:
There were a number of models of MacBook Pros from 2010 to 2014, and iMacs with 
NVIDIA GPU’s included, as well as off the shelf PCIe cards in the large tower 
macs from that time. When they moved to the “trash can” tower models and 
post-2014 MBPs, the option for NVIDIA GPU hardware was dropped and longer 
available. MacOS 10.14 removed 3rd party driver support. XCode 10.1 wasn’t 
around for long and there was some strangeness around helper files, removing 
them makes the problems go away. Most mac users moved on so never ran into 
these issues.

Notes on new installs of High Sierra:

1. Apple seems to have removed High Sierra installers off of their apt-store 
servers, and even archive.org doesn’t seem to have a copy. Finding a working 
macOS 10.13 USB thumb drive installer someone made a dozen years ago might be 
the hardest part of following this project.
2. The certificates on surviving USB installers have expired, so the first step 
is to reset the clock on the system to be installed back to October 2017, after 
it was released but well before when the certs expired. Once installed and 
booting, the system will connect to an NTP server and be set back to the 
current date and time.
3. After installing, you should, and can still update your system to 10.13.6. 

You’ll need to get XCode 10.1, the last version supported under High Sierra. 
This is now buried on developer.apple.com but still available in their old 
versions repo, external search engines can help find it. Having a developers 
subscription might make it easier to locate, but that should not be required. 

You’ll also need the Apple Command Line Tools for XCode 10.1 and macOS 10.13.6.

You’ll want MacPorts for High Sierra. Getting gmake, autoconf, git, vim, etc. 
is as easy as “port install X”. They’re doing an awesome job keeping things 
updated on all macOS versions.

Notes on NVIDIA stuffs:

The web graphics driver and CUDA 10.1 for macOS should still be available on 
NVIDIA’s website. Install these after updating to 10.13.6.

Notes on install scripts:

MacPorts keeps files in /opt/local/###, default builds usually land in 
/usr/local/###, so I’ve chosen to place all this project’s build artifacts into 
/opt/tools/###. A global settings file “0000_env” controls this, and other 
build environment settings like number of build threads to use. If /opt/tools 
is “sudo chown <USERNAME>:staff”, where <USERNAME> is your userID, the build 
scripts can be run as that user rather than root.

Before building Python 3.14.7, the script “00_xz” and “085_openssl” should be 
run to install the latest working libraries. The python installer also builds 
pip, which depends on openssl to connect to servers.

The “0890_python” script builds and installs Python. The package and build 
areas are in the same working area as where the scripts are installed, so 
you’ll need about 700MB for openssl, 250MB of scratch space for Python, 400MB 
of space to build numpy, and 6GB(!!) to build pytorch. 

Later versions of pytorch drop CUDA compatibility 3.0 support, so can’t be used 
with the hardware on these old macs. Later versions of numpy 2.5.x assume 
advanced AVX512 intrinsics that XCode 10.1 doesn’t support, even when the build 
flags say not to use : “-Csetup-args=-Dcpu-dispatch=”max -X86_V4””, some 
developer running on newer systems has been making changes that break older 
platform builds, probably without knowing it.

If there’s only one person that’s ever gone down this path, it’s probably not 
worth fixing.

Hopefully this is interesting. Read the other doc to find out why this project 
ended up being worth well over four billion dollars.
