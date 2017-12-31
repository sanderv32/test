#!/usr/bin/env python
# coding=utf-8

from __future__ import print_function

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
GH_RELEASE = """
{{
  "tag_name": "{tag_name}",
  "target_commitish": "master",
  "name": "{name}",
  "body": "{body}",
  "draft": false,
  "prerelease": false
}}"""


class DIR(object):
    """
    Directory sort class
    """

    @classmethod
    def list(cls, directory=None):
        dirlist = []
        if directory is None:
            raise Exception("directory in mandatory")
        for dirname, _, filelist in os.walk(directory):
            for f in filelist:
                dirlist.append(dirname + "/" + f)
        dirlist.sort()
        for f in dirlist:
            yield f


class TAR(object):
    """
    TAR Class
    """

    @classmethod
    def write(cls, filename=None):
        """
        Write tar.gz file

        :param filename:    Filename of the tar file
        """
        if filename is None:
            raise Exception("filename is mandatory")
        with tarfile.open(filename, mode="w:gz") as archive:
            archive.add(TMP_DIR, recursive=True, filter=cls.filter)

    @staticmethod
    def filter(tarinfo):
        """
        Filter function which will filter out .git directory

        :param tarinfo: TarInfo given to filter
        :return:        Returns the path if doesn't match filter otherwise None
        """
        tarinfo.path = tarinfo.path.replace(TMP_DIR, ARCHIVE_PATH)
        if "/.git" in tarinfo.name or "/.git/" in tarinfo.name:
            return None
        return tarinfo


def main():
    """
    MAIN Function
    """
    exitcode = 0
    manifest_file = "manifest.json"
    with open(manifest_file) as f:
        manifest_data = json.load(f, object_pairs_hook=OrderedDict)

    # Checkout submodule
    subprocess.call(['git', 'submodule', 'update'])
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

            with open(filename) as f:
                sha1sum = hashlib.sha1(f.read()).hexdigest()

            release_entry = OrderedDict([
                ('url', URL.format(filename=filename)),
                ('sha1', sha1sum),
                ('version', tag[1:] if tag[0] == "v" else tag)
            ])
            if tag == "master":
                if manifest_data['framework-esp8266-nonos-sdk'][0]['version'] == "master":
                    del manifest_data['framework-esp8266-nonos-sdk'][0]
            manifest_data['framework-esp8266-nonos-sdk'].insert(0, release_entry)
        with open(manifest_file, "w") as f:
            f.write(json.dumps(manifest_data, indent=2))
    except Exception as err:
        print(err.message)
        exitcode = 1
    sys.exit(exitcode)


if __name__ == '__main__':
    main()
