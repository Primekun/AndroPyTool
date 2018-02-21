import os
import sys
import argparse
import subprocess

from tqdm import tqdm
from threading import Timer
from termcolor import colored
from os.path import join as join_dir
from argparse import RawTextHelpFormatter

working_directory = os.getcwd() + "/"

kill = lambda process: process.kill()

MAX_TIME_ANALYSIS = 30  # Minutes
FLOWDROID_FOLDER = working_directory + "FlowDroid/"

# FlowDroid authors recommend to use the official platforms downloaded from Google, not the ones from GitHub, for better
# performance
ANDROID_PLATFORMS_FOLDER = working_directory + 'FlowDroid/android-platforms/platforms'

MAX_MEMORY = 80  # GIGABYTES

LIBRARIES_FLOWDROID = "soot-trunk.jar:soot-infoflow.jar:soot-infoflow-android.jar:slf4j-api-1.7.5.jar:slf4j-simple-" \
                      "1.7.5.jar:axml-2.0.jar"

FLOWDROID_MAIN_CALL = "soot.jimple.infoflow.android.TestApps.Test"


# https://github.com/secure-software-engineering/soot-infoflow-android/wiki

def print_message(message, with_color, color):
    if with_color:
        print colored(message, color)
    else:
        print message


def get_call_flowdroid(apk_path):
    flowdroid_call_list = ["java",  # A list to later build a string space separated
                           "-Xmx" + str(MAX_MEMORY) + "g",
                           "-cp",
                           LIBRARIES_FLOWDROID,
                           FLOWDROID_MAIN_CALL,
                           apk_path,
                           ANDROID_PLATFORMS_FOLDER]

    return " ".join(flowdroid_call_list)


def main():
    parser = argparse.ArgumentParser(
        description="Launches FlowDroid\n\n", formatter_class=RawTextHelpFormatter)

    parser.add_argument('-s', '--source', help='Source directory for APKs', required=True)

    parser.add_argument('-o', '--output', help='Output directory', required=True)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()

    run_flowdroid(source_directory=args.source,
                  output_folder=args.output)


def run_flowdroid(source_directory, output_folder, with_color=True):
    """
    Executes flowdroid over a set of samples

    Parameters
    ----------
    :param source_directory: Folder containing apk files
    :param output_folder: Folder where files generated by FlowDroid are saved
    :param with_color: If colors are used to print messages
    """
    if not os.path.exists(source_directory):
        print print_message("Folder not found!", with_color, 'red')

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    list_apks = []
    for path, subdirs, files in os.walk(source_directory):
        for name in files:
            if name.endswith(".apk"):
                list_apks.append(os.path.join(path, name))

    for apk_path in tqdm(list_apks):

        apk_id = os.path.basename(apk_path)
        print "RUNNING FLOWDROID FOR: " + str(apk_id)

        if os.path.isfile(join_dir(output_folder, apk_id.replace(".apk", ".json"))) or "assets" in apk_id:
            continue
        print "TRUE TRUE TRUE"
        flowdroid_call = get_call_flowdroid(apk_path)

        origen_wd = os.getcwd()
        os.chdir(os.path.join(os.path.abspath(sys.path[0]), FLOWDROID_FOLDER))

        process = subprocess.Popen(flowdroid_call, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)  # , env={'PATH': FLOWDROID_FOLDER})

        os.chdir(origen_wd)  # get back to our original working directory

        timer = Timer(MAX_TIME_ANALYSIS * 60, kill, [process])
        try:
            timer.start()
            stdout, stderr = process.communicate()

        finally:
            timer.cancel()

        with open(join_dir(output_folder, apk_id.replace(".apk", ".json")), "w") as output:
            output.write(str(stdout))

if __name__ == '__main__':
    main()
