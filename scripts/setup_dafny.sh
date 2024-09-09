#!/bin/bash
author=$1
branch=$2

git clone https://github.com/dafny-lang/dafny.git
cd dafny
git remote add merge-head https://github.com/$author/dafny.git
git fetch merge-head
git checkout -b $branch merge-head/$branch
retry_count=0
while [ $retry_count -lt 10 ]
do
    make exe
    if [ $? -eq 0 ]; then
        break
    fi
    retry_count=$((retry_count+1))
done

if [ $retry_count -eq 10 ]; then
    exit 1
fi
make z3-ubuntu

exit 0