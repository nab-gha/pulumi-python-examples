import pulumi
import pulumi_aws as aws


class NetworkingComponentArgs:
    def __init__(
        self,
        prefix,
        internal_lb,
        vpc_id=None,
        private_subnet_ids=[],
        public_subnet_ids=[],
        num_availability_zones=1,
        cidr_block="10.0.0.0/16",
        public_subnet_cidr_blocks=["10.0.0.0/24"],
        private_subnet_cidr_blocks=["10.0.1.0/24"],
    ):
        self.prefix = prefix.replace('_', '-')
        self.internal_lb = internal_lb
        self.cidr_block = cidr_block
        self.num_availability_zones = num_availability_zones
        self.public_subnet_cidr_blocks = public_subnet_cidr_blocks
        self.private_subnet_cidr_blocks = private_subnet_cidr_blocks
        self.vpc_id = vpc_id
        self.private_subnet_ids = private_subnet_ids
        self.public_subnet_ids = public_subnet_ids
        self.create_vpc = False
        if self.vpc_id:
            assert len(self.public_subnet_ids) == self.num_availability_zones
            assert len(self.private_subnet_ids) == self.num_availability_zones
        else:
            assert len(self.public_subnet_cidr_blocks) == self.num_availability_zones
            assert len(self.private_subnet_cidr_blocks) == self.num_availability_zones
            self.create_vpc = True

def build_port_mapping(source,destination):
    return { "source": source, "destination": destination }
class NetworkingComponent(pulumi.ComponentResource):
    def __init__(self, name, args: NetworkingComponentArgs, opts=None):
        super().__init__("pkg:index:NetworkingComponent", name, None, opts)
        self.ports = [build_port_mapping(22,22)]
        self.vpc = None
        self.igw = None
        self.route_table = None
        self.subnets = []
        self.public_subnets = []
        self.private_subnets = []

        if args.create_vpc:
            self.vpc = aws.ec2.Vpc(
                "vpc",
                cidr_block=args.cidr_block,
                tags={"Name": "Example One"},
                opts=pulumi.ResourceOptions(parent=self),
            )

            self.igw = aws.ec2.InternetGateway(
                "igw", vpc_id=self.vpc.id, opts=pulumi.ResourceOptions(parent=self)
            )

            self.route_table = aws.ec2.RouteTable(
                "route_table",
                vpc_id=self.vpc.id,
                routes=[
                    aws.ec2.RouteTableRouteArgs(
                        cidr_block="0.0.0.0/0",
                        gateway_id=self.igw.id,
                    )
                ],
                opts=pulumi.ResourceOptions(parent=self),
            )

            all_azs = aws.get_availability_zones()
            availability_zones = all_azs.names[: args.num_availability_zones]

            self.nat_gws = {}

            for index, az in enumerate(availability_zones):
                public_subnet = aws.ec2.Subnet(
                    f"public-{az}",
                    vpc_id=self.vpc.id,
                    map_public_ip_on_launch=True,
                    cidr_block=args.public_subnet_cidr_blocks[index],
                    availability_zone=az,
                    tags={"Name": f"public-{az}"},
                    opts=pulumi.ResourceOptions(parent=self),
                )
                aws.ec2.RouteTableAssociation(
                    f"rt-association-public-{az}",
                    route_table_id=self.route_table.id,
                    subnet_id=public_subnet.id,
                    opts=pulumi.ResourceOptions(parent=self),
                )
                self.subnets.append(public_subnet)
                self.public_subnets.append(public_subnet)

                eip = aws.ec2.Eip(
                    f"nat-gw-eip-{az}",
                    vpc=True,
                    opts=pulumi.ResourceOptions(parent=self),
                )

                self.nat_gws[az] = aws.ec2.NatGateway(
                    f"nat-gw-{az}",
                    subnet_id=public_subnet.id,
                    allocation_id=eip.id,
                    opts=pulumi.ResourceOptions(parent=self),
                )

                private_route_table = aws.ec2.RouteTable(
                    f"private-route-table-{az}",
                    vpc_id=self.vpc.id,
                    routes=[
                        aws.ec2.RouteTableRouteArgs(
                            cidr_block="0.0.0.0/0",
                            nat_gateway_id=self.nat_gws[az].id,
                        )
                    ],
                    opts=pulumi.ResourceOptions(parent=self),
                )

                private_subnet = aws.ec2.Subnet(
                    f"private-{az}",
                    vpc_id=self.vpc.id,
                    map_public_ip_on_launch=False,
                    cidr_block=args.private_subnet_cidr_blocks[index],
                    availability_zone=az,
                    tags={"Name": f"private-{az}"},
                    opts=pulumi.ResourceOptions(parent=self),
                )
                aws.ec2.RouteTableAssociation(
                    f"rt-association-private-{az}",
                    route_table_id=private_route_table.id,
                    subnet_id=private_subnet.id,
                    opts=pulumi.ResourceOptions(parent=self),
                )
                self.subnets.append(private_subnet)
                self.private_subnets.append(private_subnet)
        else:
            self.vpc = aws.ec2.Vpc.get(
                "vpc",
                id=args.vpc_id,
                opts=pulumi.ResourceOptions(parent=self),
            )

            # TODO: not sure if it's feasible to get the AZ here for the pulumi resource name
            for index, private_subnet_id in enumerate(args.private_subnet_ids):
                private_subnet = aws.ec2.Subnet.get(
                    f"private-{index}",
                    id=private_subnet_id,
                    opts=pulumi.ResourceOptions(parent=self),
                )
                self.subnets.append(private_subnet)
                self.private_subnets.append(private_subnet)

            for index, public_subnet_id in enumerate(args.private_subnet_ids):
                public_subnet = aws.ec2.Subnet.get(
                    f"public-{index}",
                    id=public_subnet_id,
                    opts=pulumi.ResourceOptions(parent=self),
                )
                self.subnets.append(public_subnet)
                self.public_subnets.append(public_subnet)

        self.internal_sg = aws.ec2.SecurityGroup(
            "internalSg",
            description="Allow all nodes to talk to each other",
            vpc_id=self.vpc.id,
            tags={"Name": "Internal security group"},
            opts=pulumi.ResourceOptions(parent=self),
        )

        aws.ec2.SecurityGroupRule(
            "allowInternalEgress",
            type="egress",
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
            ipv6_cidr_blocks=["::/0"],
            security_group_id=self.internal_sg.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        aws.ec2.SecurityGroupRule(
            "allowInternalIngress",
            type="ingress",
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=[self.vpc.cidr_block],
            security_group_id=self.internal_sg.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.ghes_sg = aws.ec2.SecurityGroup(
            "ghesSg",
            description="Allow ghes access",
            vpc_id=self.vpc.id,
            ingress=[
                {
                    "protocol": "tcp",
                    "from_port": port["source"],
                    "to_port": port["destination"],
                    "cidr_blocks": ["0.0.0.0/0"],
                }
                for port in self.ghes_ports
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                    cidr_blocks=["0.0.0.0/0"],
                    ipv6_cidr_blocks=["::/0"],
                )
            ],
            tags={"Name": "External security group"},
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.ghes_lb = aws.lb.LoadBalancer(
            "ghes-load-balancer",
            internal=args.internal_lb,
            load_balancer_type="network",
            subnets=[subnet.id for subnet in self.public_subnets],
            tags={"Name": f"{args.prefix}load balancer"},
            opts=pulumi.ResourceOptions(parent=self),
        )
        
        self.ghes_target_groups = {}
        self.ghes_listeners = {}
        for port in self.ghes_ports:
            tg = aws.lb.TargetGroup(
                f"ghes-lb-tg-{port['destination']}",
                port=port["destination"],
                protocol="TCP",
                vpc_id=self.vpc.id,
                # the 'args.internal_lb' contains [True/False]
                proxy_protocol_v2=args.internal_lb,
                opts=pulumi.ResourceOptions(parent=self),
            )
            self.ghes_target_groups[port["source"]] = tg

            self.ghes_listeners[port["source"]] = aws.lb.Listener(
                f"ghes-lb-listener-{port['source']}",
                load_balancer_arn=self.ghes_lb.arn,
                port=port['source'],
                protocol="TCP",

                default_actions=[
                    aws.lb.ListenerDefaultActionArgs(
                        type="forward",
                        target_group_arn=tg.arn,
                    )
                ],
                opts=pulumi.ResourceOptions(parent=self),
            )

        pulumi.export("vpcId", self.vpc.id)
        pulumi.export("LB-DNS-Name", self.ghes_lb.dns_name)
        self.register_outputs(
            {
                "vpcId": self.vpc.id,
                "LB-DNS-Name": self.ghes_lb.dns_name
            }
        )
    
        pulumi.export("Loadbalancer_DNS", self.ghes_lb.dns_name)
