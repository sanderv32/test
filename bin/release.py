#!/usr/bin/env python
"""This program creates new .tar.gz version of the ESP8266-NONOS-SDK Repo."""
# coding=utf-8

from __future__ import print_function

import hashlib
import json
import os
import subprocess
import sys
import tarfile
from collections import OrderedDict

URL = ("https://github.com/sanderv32/framework-esp8266-nonos-sdk"
       "/raw/master/{filename}")
SDK = "ESP8266_NONOS_SDK"
ARCHIVE_PATH = "ESP8266_NONOS_SDK-master"
TMP_DIR = "ESP8266_NONOS_SDK-master"
CACHE_DIR = ".cache"
CACHED_SHA1 = "%s/master-sha1.txt" % CACHE_DIR
GH_RELEASE = """
{{
  "tag_name": "{tag_name}",
  "target_commitish": "master",
  "name": "{name}",
  "body": "{body}",
  "draft": false,
  "prerelease": false
}}"""


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
    exitcode = 0
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

            filename = "%s-%s.tar.gz" % (SDK, tag[1:] if tag[0] == "v" else tag)
            if os.path.exists(filename) and tag != "master":
                continue
            print("Creating archive: %s" % filename)
            TAR.write(filename)

            with open(filename) as f_archive:
                sha1sum = hashlib.sha1(f_archive.read()).hexdigest()

            release_entry = OrderedDict([
                ('url', URL.format(filename=filename)),
                ('sha1', sha1sum),
                ('version', tag[1:] if tag[0] == "v" else tag)
            ])
            master = manifest_data['framework-esp8266-nonos-sdk'][0]
            if tag == "master":
                if os.path.exists(CACHED_SHA1):
                    # CACHED_SHA1 exists in cache directory, lets compare it with current master SHA1
                    with open(CACHED_SHA1, "r") as f_sha1:
                        cached_sha1 = f_sha1.read()
                    current_sha1 = subprocess.check_output(["git", "rev-parse", "HEAD"])
                    print("'%s' , '%s'" % (cached_sha1, current_sha1))
                    if current_sha1 == cached_sha1:
                        # Master SHA1 is the same like previous build so skip master
                        print("Master branch didn't change, skipping...")
                        continue
                # CACHED_SHA1 doesn't exist, write current master SHA1
                print("New master branch, creating new archive...")
                current_sha1 = subprocess.check_output(["git", "rev-parse", "HEAD"])
                with open(CACHED_SHA1, "w") as f_sha1:
                    f_sha1.write(current_sha1)

                if master['version'] == "master":
                    del manifest_data['framework-esp8266-nonos-sdk'][0]
            manifest_data['framework-esp8266-nonos-sdk'].insert(0, release_entry)
        with open(manifest_file, "w") as f_manifest:
            f_manifest.write(json.dumps(manifest_data, indent=2))

    except Exception as err:
        print(err.message)
        exitcode = 1
    sys.exit(exitcode)


if __name__ == '__main__':
    main()
