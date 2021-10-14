# Pulumi Python Examples

## Goals

Pulumi Python examples used to explore issues and approaches

- Infrastructure as Code - Define all infrastructure using tooling such as [Pulumi](https://www.pulumi.com)

## Setup
Install required software and setup environment
### Pulumi

The *Infrastructure as Code* tool.

- [Install Pulumi](https://www.pulumi.com/docs/get-started/install/)
### AWS

An AWS account and the AWS CLI 

- [Install AWS CLI version 2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-mac.html)

### Python

- Install Python3
- setup virtual environment
  - cd to `example1` and create virtual env
  - `virtualenv venv`
  - `source venv/bin/activate`

### Building Dev Cluster

- Deploy infrasturcture
  - create an S3 bucket and a prefix (folder) for storing your pulumi state 
  - `export PULUMI_CONFIG_PASSPHRASE=""`
  - `pulumi --non-interactive login s3://<bucket>/<prefix>`
  - `pulumi --non-interactive stack select -c example-one`
  - `pulumi up`

### Running unittests

Reading Pulumi issues, documentation and blogs, I think this should work:

    export PULUMI_PYTHON_PROJECT=example-one
    export PULUMI_PYTHON_STACK=example-one
    export PULUMI_CONFIG=$(yq eval Pulumi.${PULUMI_PYTHON_STACK}.yaml --output-format=json | jq -c '.config')
    pytest

But it fails

    ERROR test_server.py - pulumi.config.ConfigMissingError: Missing required configuration variable 'project:application'