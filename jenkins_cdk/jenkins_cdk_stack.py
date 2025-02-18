from aws_cdk import (
    Duration,
    IResource,
    RemovalPolicy,
    Stack,
    Tags,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_efs as efs,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct


class JenkinsCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_name = "jenkins-cdk"
        jenkins_home_dir = "jenkins-home"

        cluster = ecs.Cluster(self, f"{app_name}-cluster", cluster_name=app_name)

        fs = efs.FileSystem(
            self,
            f"{app_name}-efs",
            vpc=cluster.vpc,
            file_system_name=app_name,
            removal_policy=RemovalPolicy.DESTROY,
        )

        access_point = fs.add_access_point(
            f"{app_name}-ap",
            path=f"/{jenkins_home_dir}",
            posix_user=efs.PosixUser(gid="1000", uid="1000"),
            create_acl=efs.Acl(owner_gid="1000", owner_uid="1000", permissions="755"),
        )

        task_definition = ecs.FargateTaskDefinition(
            self, f"{app_name}-task", family=app_name, cpu=1024, memory_limit_mib=2048
        )

        task_definition.add_volume(
            name=jenkins_home_dir,
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=fs.file_system_id,
                transit_encryption="ENABLED",
                authorization_config=ecs.AuthorizationConfig(
                    access_point_id=access_point.access_point_id, iam="ENABLED"
                ),
            ),
        )

        container_definition = task_definition.add_container(
            app_name,
            image=ecs.ContainerImage.from_registry("jenkins/jenkins:2.497"),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="jenkins"),
            port_mappings=[ecs.PortMapping(container_port=8080)],
        )

        container_definition.add_mount_points(
            ecs.MountPoint(
                container_path=f"/var/jenkins_home",
                source_volume=jenkins_home_dir,
                read_only=False,
            )
        )

        fargate_service = ecs.FargateService(
            self,
            f"{app_name}-service",
            service_name=app_name,
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            max_healthy_percent=100,
            min_healthy_percent=0,
            health_check_grace_period=Duration.minutes(5),
        )
        fargate_service.connections.allow_to(fs, port_range=ec2.Port.tcp(2049))

        load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            f"{app_name}-elb",
            load_balancer_name=app_name,
            vpc=cluster.vpc,
            internet_facing=True,
        )

        lb_listener = load_balancer.add_listener(
            f"{app_name}-listener",
            port=80,
        )

        lb_target = lb_listener.add_targets(
            f"{app_name}-target",
            port=8080,
            targets=[fargate_service],
            deregistration_delay=Duration.seconds(10),
            health_check=elbv2.HealthCheck(path="/login"),
        )
