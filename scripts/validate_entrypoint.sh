#!/bin/bash

COMMIT=$1
fileDir=$2

touch $COMMIT-result
aws s3 cp $fileDir/main.dfy .
aws s3 cp $fileDir/interestingness_test.sh .
chmod +x interestingness_test.sh
./interestingness_test.sh 2>&1
echo $? >> $COMMIT-result
aws s3 cp $COMMIT-result $fileDir/validations/