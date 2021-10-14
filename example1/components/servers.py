import pulumi
import pulumi_aws as aws
from pulumi import Output

CANONICAL_AMI_ID = "TBD"

class ServerComponentArgs:
    def __init__(
        self,
        name,
        subnet_id,
        vpc_security_group_ids,
        key,
        server_role,
        index,
        lb_dns,
        private_ips,
        root_volume_size=200,
        root_volume_type="gp2",
        data_volume_size=200,
        data_volume_type="gp2",
        ex1_ami_owner="482649550366",
        instance_type="t2.micro",
        stack_name=None,
    ):
        self.subnet_id = subnet_id
        self.name = name
        self.instance_type = instance_type
        self.key = key
        self.server_role = server_role
        self.index = index
        self.lb_dns = lb_dns
        self.root_volume_size = root_volume_size
        self.root_volume_type = root_volume_type
        self.data_volume_size = data_volume_size
        self.data_volume_type = data_volume_type
        self.ex1_ami_owner = ex1_ami_owner
        self.vpc_security_group_ids = vpc_security_group_ids
        self.private_ips = private_ips
        self.stack_name = stack_name

class ServerComponent(pulumi.ComponentResource):
    user_data_file = "./components/server_user_data.sh"
    def __init__(self, name, args: ServerComponentArgs, opts=None):
        super().__init__("pkg:index:ServerComponent", name, None, opts)

        self.ami = self.get_ami(args)

        instance_profile = aws.iam.InstanceProfile(
            f"instance-profile-{args.name}",
            opts=pulumi.ResourceOptions(parent=self),
        )

        network_interface = aws.ec2.NetworkInterface(
            f"network-interface-{args.name}",
            subnet_id=args.subnet_id,
            private_ips=args.private_ips,
            security_groups=args.vpc_security_group_ids,
            opts=pulumi.ResourceOptions(parent=self),
        )

        user_data = self.get_user_data(args)

        self.instance = aws.ec2.Instance(
            f"instance-{args.name}",
            instance_type=args.instance_type,
            ebs_block_devices=[
                aws.ec2.InstanceEbsBlockDeviceArgs(
                    device_name="/dev/xvdf",
                    volume_type=args.data_volume_type,
                    volume_size=args.data_volume_size,
                    encrypted=True,
                )
            ],
            root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
                volume_type=args.root_volume_type,
                volume_size=args.root_volume_size,
                encrypted=True,
            ),
            network_interfaces=[
                aws.ec2.InstanceNetworkInterfaceArgs(
                    network_interface_id=network_interface.id,
                    device_index=0,
                )
            ],
            key_name=args.key,
            user_data=user_data,
            ami=self.ami.id,
            iam_instance_profile=instance_profile,
            tags={"Name": args.name},
            opts=pulumi.ResourceOptions(parent=self),
        )
        pulumi.export(f"InstanceId-{args.server_role}-{args.index}", self.instance.id)

    def get_user_data(self, args):
        return Output.all(
            args.server_role,
            args.index,
            args.lb_dns,
        ).apply(
            lambda args: (
                open(self.user_data_file)
                .read()
                .format(
                    server_role=args[0],
                    index=args[1],
                    lb_dns=args[2]
                )
            )
        )

    def get_ami(self, args):
        return aws.ec2.get_ami(
            most_recent="true",
            owners=[args.ex1_ami_owner],
        )

class BackupServerComponent(ServerComponent):
    user_data_file = "./components/backup_user_data.sh"
    def __init__(self, *args, **kwargs):
        super(BackupServerComponent, self).__init__(*args, **kwargs)

    def get_ami(self, args):
        return aws.ec2.get_ami(
            most_recent="true",
            name_regex="ubuntu-focal-20.04-amd64"

        )