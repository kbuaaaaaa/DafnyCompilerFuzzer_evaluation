#!/bin/bash
COMMIT=${1:-$(git rev-parse BISECT_HEAD)}

echo "Bisecting at commit $COMMIT"

git checkout $COMMIT
echo "Building Dafny"
# Check if the make command failed
if ! make exe; then
  make clean
  make exe
fi

echo "Building Z3"
yes All | make z3-ubuntu > /dev/null 2>&1
cd ..

echo "Running interestingness test"
timeout 600 ./interestingness_test.sh 2>&1
exit_status=$?

# If the timeout is reached, exit with status 125 to indicate the commit should be skipped
if [ $exit_status -eq 1 ]; then
  echo "Result of commit $COMMIT is good."
  exit 0
elif [ $exit_status -eq 0 ]; then
  echo "Result of commit $COMMIT is bad."
  exit 1
else
  echo "Result of commit $COMMIT is $exit_status."
  exit 125
fi


