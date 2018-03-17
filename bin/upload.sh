#!/usr/bin/env bash

[ -n "$DEBUG" ] && set -x

git checkout master

git config --global user.email "$GIT_EMAIL"
git config --global user.name "$GIT_USERNAME"

git remote rm origin
git remote add origin https://$GITHUB_USER:$GITHUB_API_KEY@$GITHUB_REPO
git add -f *.tar.gz *.json
git commit -m "Travis build $TRAVIS_BUILD_NUMBER pushed [skip ci] "
git push -fq origin master > /dev/null
echo -e "Done\n"
