#!/usr/bin/env bash

PreflightSteps () {{
    echo "Updating system packages & installing Zip"
    echo "deb http://deb.debian.org/debian stretch main" > /etc/apt/sources.list
    apt-get update -y
    apt-get install -y unzip

    echo "Installing AWS CLI"
    TMPDIR=$(mktemp -d)
    cd $TMPDIR
    echo "Downloading AWS CLI"
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    ./aws/install

    echo "Downloading SSM Agent"
    # TODO: parameterize the region
    n=0
    until [ "$n" -ge 20 ]
    do
        wget -q https://s3.us-east-2.amazonaws.com/amazon-ssm-us-east-2/latest/debian_amd64/amazon-ssm-agent.deb && break
        n=$((n+1))
        sleep 15
    done
    echo "Installing SSM Agent"
    dpkg -i amazon-ssm-agent.deb

    echo "Downloading CloudWatch Agent"
    n=0
    until [ "$n" -ge 20 ]
    do
        wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/debian/amd64/latest/amazon-cloudwatch-agent.deb && break
        n=$((n+1))
        sleep 15
    done
    echo "Installing CloudWatch Agent"
    dpkg -i -E amazon-cloudwatch-agent.deb
}}

# All Nodes
echo "Entering Pre-Flight Steps"
PreflightSteps

# check that the 'cluster setup' runs ONLY on the main DB host
if [ "{index}" = "0" ] && [ "{server_role}" = "db" ]; then
    echo "Current role is: {server_role} - Starting Cluster Config"
    # RunConfigPass
fi 
