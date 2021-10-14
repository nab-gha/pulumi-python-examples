import pulumi
from pulumi import Output
import pulumi_aws as aws
from components import networking,servers
import json

stack = pulumi.get_stack()

config = pulumi.Config()
app_config = config.require_object("application")
network_config = config.require_object("networking")
server_config = config.require_object("servers")
server_roles = ["frontend", "db"]

networking = networking.NetworkingComponent(
    "networking",
    networking.NetworkingComponentArgs(
        internal_lb=network_config.get("internal_lb"),
        prefix=f"{stack}-",
        cidr_block=network_config.get("vpc_cidr"),
        vpc_id=network_config.get("vpc_id"),
        num_availability_zones=network_config.get("num_azs"),
        public_subnet_cidr_blocks=network_config.get("public_subnet_cidr"),
        private_subnet_cidr_blocks=network_config.get("private_subnet_cidr"),
        public_subnet_ids=network_config.get("public_subnet_id"),
        private_subnet_ids=network_config.get("private_subnet_id"),
    ),
)

server_types = {
    "frontend": [],
    "db": [],
}

server_list = {role: [] for role in server_roles}
for role in server_roles:
    if role in server_config:
        for index, conf in enumerate(server_config[role]["nodes"]):
            ip = conf["ip"]
            security_groups = [networking.internal_sg.id]
            serverComponent = servers.ServerComponent
            if role == "frontend":
                security_groups.append(networking.ex1_sg.id)

            serverArgs = servers.ServerComponentArgs(
                name=f"{stack}_cluster_{role}-server-{index}",
                subnet_id=networking.private_subnets[0].id,
                private_ips=[ip],
                key=app_config["key"],
                server_role=role,
                index=index,
                lb_dns=networking.ex1_lb.dns_name,
                vpc_security_group_ids=security_groups,
                instance_type=server_config[role]["instance_type"],
                data_volume_size=server_config[role]["volume_size"],
                stack_name=stack,
            )
            server_list[role].append(
                serverComponent(
                    f"server-{role}-{index}",
                    serverArgs,
                )
            )

# TODO: eventually this should be an autoscaling group
for index, server in enumerate(server_list["frontend"]):
    for port, tg in networking.ex1_target_groups.items():
        aws.lb.TargetGroupAttachment(
            f"tg-attachment-{index}-{port}",
            target_group_arn=tg.arn,
            target_id=server_list["frontend"][index].instance.id,
            port= list(filter(lambda p: p['source'] == port, networking.ex1_ports))[0]['destination'],
        )
