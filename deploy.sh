#!/bin/bash

if [ -z "$1" ]
  then
    echo "please provide a bucket to upload artifacts required for the cloudformation template"
    exit 1
fi

aws cloudformation package --template-file cf.yml --s3-bucket $1 --output-template .packaged-template.yml $2 $3
aws cloudformation deploy --template-file .packaged-template.yml --capabilities CAPABILITY_IAM --stack-name FLOWS-clevver $2 $3
