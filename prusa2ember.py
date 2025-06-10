#
# prusa2ember.py
#
# A silly script to convert Prusa SL1 stereolithography print jobs to work with the Autodesk Ember printer
#
# Copyright 2025 drmn4ea "at" gmail
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#
#

import zipfile
import tarfile
import argparse
import os
import shutil

# Temporary output folder to unpack intermediate contents to
output_folder = './output'

# Default printsettings file content
default_settings_file = '{"Settings":{"LayerThicknessMicrons":50,"JobName":"dummy_name.stl","BurnInExposureSec":4.0,"BurnInLayers":4,"FirstExposureSec":10.0,"ModelExposureSec":2.75,"FirstSeparationRPM":6,"FirstApproachRPM":6,"FirstZLiftMicrons":2000,"FirstSeparationMicronsPerSec":3000,"FirstApproachMicronsPerSec":5000,"FirstRotationMilliDegrees":60000,"FirstExposureWaitMS":0,"FirstSeparationWaitMS":0,"FirstApproachWaitMS":0,"BurnInSeparationRPM":11,"BurnInApproachRPM":11,"BurnInZLiftMicrons":2000,"BurnInSeparationMicronsPerSec":3000,"BurnInApproachMicronsPerSec":5000,"BurnInRotationMilliDegrees":60000,"BurnInExposureWaitMS":0,"BurnInSeparationWaitMS":0,"BurnInApproachWaitMS":0,"ModelSeparationRPM":12,"ModelApproachRPM":12,"ModelZLiftMicrons":1000,"ModelSeparationMicronsPerSec":5000,"ModelApproachMicronsPerSec":5000,"ModelRotationMilliDegrees":60000,"ModelExposureWaitMS":0,"ModelSeparationWaitMS":0,"ModelApproachWaitMS":0,"JobID":"1234"}}'

def get_sorted(directory, extension):
    """
    Returns a sorted list of files in the given directory that have the specified extension.

    Args:
        directory (str): The path to the directory.
        extension (str): The file extension to filter by (e.g., ".txt", ".pdf").

    Returns:
        list: A sorted list of file names with the specified extension.
               Returns an empty list if no files match the criteria.
    """
    files = [f for f in os.listdir(directory) if f.endswith(extension)]
    return sorted(files)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("fname", help="Sliced file to repack (Prusa Research SL1 format)")
    parser.add_argument("-s", "--settingsfile", help="Pass alternate settings file")
    parser.add_argument("-v", "--verbose", help="Verbose output", action = "store_true")
    args = parser.parse_args()

    cwd = os.getcwd()
    print(f"CWD is: {cwd}")

    try:
        shutil.rmtree(output_folder)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    #Unzip all contents t
    # o a target directory
    with zipfile.ZipFile(args.fname, 'r') as zip_ref:
        znames = zip_ref.namelist()
        if args.verbose:
            print("Found the following input files:")
            print(znames)
        # filter the names to include just the PNGs not in a subfolder (thumbnails)
        znames_filtered = [x for x in znames if '.png' in x and '/' not in x]
        print("Filtering zip contents, %u input files -> %u output slices", (len(znames), len(znames_filtered)))
        zip_ref.extractall(output_folder, members=znames_filtered)

    # get the resulting file list
    pngs = get_sorted(output_folder, '.png')

    #print(pngs)

    for i in range(0, len(pngs)):
        # rename files in order to 'slice_1.png', 'slice_2.png', etc.
        os.rename(output_folder + '/' + pngs[i], output_folder + '/' + f"slice_{i+1}.png")

    # Write the default settings file. We should really adjust the exposure time at least, but this works for now.
    if args.settingsfile:
        with open(args.settingsfile, 'r') as f_in:
            print("Reading alterante printsettings from file: %s" % f_in)
            settings_content = f_in.read()
    else:
        print("Using default printsettings")
        settings_content = default_settings_file
    with open(output_folder + '/printsettings', 'wt') as f:
        f.write(settings_content)

    # now repack the output folder contents into a .tar.gz.
    with tarfile.open(args.fname + '.tar.gz', "w:gz") as tar:
        flist = [f for f in os.listdir(output_folder)]
        if args.verbose:
            print("Repacking output files:")
            print(flist)
        for f in flist:
            # 'arcname' dance to strip pathing info
            tar.add(output_folder + '/' + f, arcname=f)