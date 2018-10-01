#!/usr/bin/env python
"""This program creates new .tar.gz version of the ESP8266-NONOS-SDK Repo."""
# coding=utf-8

from __future__ import print_function

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from collections import OrderedDict

URL = "https://github.com/sanderv32/framework-esp8266-nonos-sdk/raw/master/{filename}"
SDK = "ESP8266_NONOS_SDK"
ARCHIVE_PATH = "ESP8266_NONOS_SDK-master"
TMP_DIR = "ESP8266_NONOS_SDK-master"
CACHE_DIR = "{home}/cache".format(home=os.getenv("HOME"))
CACHED_SHA1 = "%s/master-sha1.txt" % CACHE_DIR


class Args(object):
    """ Argument class """

    def __init__(self):
        argparser = argparse.ArgumentParser()
        argparser.add_argument("-u", "--upload-script", dest="uploadscript", help="Script to upload changes",
                               required=False, action="store", default=None)
        self.__args = argparser.parse_args()

    def __getitem__(self, item):
        """ Get argument as dictionary """
        return self.__args.__dict__[item]


class TAR(object):
    """TAR Class."""

    @classmethod
    def write(cls, filename=None):
        """
        Write tar.gz file.

        :param filename:    Filename of the tar file
        """
        if filename is None:
            raise Exception("filename is mandatory")
        with tarfile.open(filename, mode="w:gz") as archive:
            archive.add(TMP_DIR, recursive=True, filter=cls.filter)

    @staticmethod
    def filter(tarinfo):
        """
        Filter function which will filter out .git directory.

        :param tarinfo: TarInfo given to filter
        :return:        Returns the path if doesn't match filter otherwise None
        """
        tarinfo.path = tarinfo.path.replace(TMP_DIR, ARCHIVE_PATH)
        if "/.git" in tarinfo.name or "/.git/" in tarinfo.name:
            return None
        return tarinfo


def main():
    """Main function of this program."""
    args = Args()
    exitcode = 0
    changed = False
    upload_script = args['uploadscript']
    manifest_file = "manifest.json"
    with open(manifest_file) as f_manifest:
        manifest_data = json.load(f_manifest, object_pairs_hook=OrderedDict)

    # Checkout submodule
    subprocess.call(['git', 'submodule', 'update'])

    # Create cache dir if it doesn't exists
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    # Create temp dir if it doesn't exists
    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    try:
        tags = subprocess.check_output(['git', 'tag'], stderr=subprocess.STDOUT, cwd=TMP_DIR).splitlines()
        tags.append("master")
        for tag in tags:
            print("Changing repo to tag: %s" % tag)
            subprocess.call(['git', 'checkout', tag], cwd=TMP_DIR)

            version = tag[1:] if tag[0] == "v" else tag
            filename = "%s-%s.tar.gz" % (SDK, version)
            if os.path.exists(filename) and tag != "master":
                continue

            print("Creating archive: %s" % filename)
            TAR.write(filename)
            changed = True

            with open(filename) as f_archive:
                sha1sum = hashlib.sha1(f_archive.read()).hexdigest()

            release_entry = OrderedDict([
                ('url', URL.format(filename=filename)),
                ('sha1', sha1sum),
                ('version', version)
            ])

            if tag == "master":
                if os.path.exists(CACHED_SHA1):
                    # CACHED_SHA1 exists in cache directory, lets compare it with current master SHA1
                    with open(CACHED_SHA1, "r") as f_sha1:
                        cached_sha1 = f_sha1.read()
                    current_sha1 = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=TMP_DIR)
                    print("Cached SHA1 : %s\nCurrent SHA1: %s" % (cached_sha1.rstrip(), current_sha1.rstrip()))
                    if current_sha1 == cached_sha1:
                        # Master SHA1 is the same like previous build so skip master
                        print("Master branch didn't change, skipping...")
                        changed = False
                        continue

                # There can only be one master, so filter out master
                manifest_data['framework-esp8266-nonos-sdk'] = \
                    filter(lambda x: x['version'] != 'master', manifest_data.get('framework-esp8266-nonos-sdk'))

                # CACHED_SHA1 doesn't exist, write current master SHA1
                print("New master branch, creating new archive...")
                current_sha1 = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=TMP_DIR)
                with open(CACHED_SHA1, "w") as f_sha1:
                    f_sha1.write(current_sha1)

            # Insert release entry in manifest dictionary
            manifest_data['framework-esp8266-nonos-sdk'].insert(0, release_entry)

        if changed:
            with open(manifest_file, "w") as f_manifest:
                f_manifest.write(json.dumps(manifest_data, indent=2))
            if upload_script:
                my_env = os.environ.copy()
                subprocess.call([upload_script], env=my_env)

    except Exception as err:
        print(err.message)
        exitcode = 1
    return exitcode


if __name__ == '__main__':
    sys.exit(main())
