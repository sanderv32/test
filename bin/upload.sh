#!/usr/bin/env bash

set -x

git checkout master

git config --global user.email "travis@verhaar.io"
git config --global user.name "Travis build bot"

git remote rm origin
git remote add origin https://sanderv32:$GITHUB_API_KEY@github.com/sanderv32/test.git
git add -f *.tar.gz *.json
git commit -m "Travis build $TRAVIS_BUILD_NUMBER pushed [skip ci] "
git push -fq origin master > /dev/null
echo -e "Done\n"