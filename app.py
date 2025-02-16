#!/usr/bin/env python3
import os

import aws_cdk as cdk

from jenkins_cdk.jenkins_cdk_stack import JenkinsCdkStack


app = cdk.App()
JenkinsCdkStack(app, "JenkinsCdkStack")

app.synth()
