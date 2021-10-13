# Pulumi Python Examples

## Goals

Pulumi Python examples used to explore issues and approaches

- Infrastructure as Code - Define all infrastructure using tooling such as [Pulumi](https://www.pulumi.com)

#### Pulumi

The *Infrastructure as Code* tool.

- [Install Pulumi](https://www.pulumi.com/docs/get-started/install/)

#### Docker

Run the Pulumi tool inside a container.

- [Install docker](https://docs.docker.com/docker-for-mac/install/)

#### AWS

An AWS account and the AWS CLI 

- [Install AWS CLI version 2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-mac.html)

---
### Building Dev Cluster

- cd to `example-one`
- Start the dev cluster
  - create an S3 bucket and a prefix (folder) for storing your pulumi state 
  - copy the `Pulumi.dev.yaml` to `Pulumi.<stack>.yaml` and name the stack the same
  - `export PULUMI_CONFIG_PASSPHRASE=""`
  - `pulumi --non-interactive login s3://<bucket>/<prefix>`
  - `pulumi --non-interactive stack select -c <stack>`
  - `pulumi up`

- Do the following on your local machine (or set your full aws config on the dev container)
  > NOTE: To use the AWS CLI to run session commands, the Session Manager plugin must also be installed on your local machine. For information, see [Install the Session Manager plugin for the AWS CLI](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html).
  - `aws --region us-west-1 ssm start-session --target <instanceid-db-0 id>`

