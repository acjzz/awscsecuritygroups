## AWScSecurityGroups stands for *AWS CloudFormation SecurityGroups*

It is a python script that helps you to create and manage security groups on amazon in an automated way.

### How does it work?
It reads a config file with the security groups and create them on a VPC in Amazon

### Dependencies:

- [boto](https://github.com/boto/boto)
- [ansible](https://github.com/ansible/ansible)
- [troposphere](https://github.com/cloudtools/troposphere)

### Getting Started

First of all, in order to use this script, you have to provide your credentials to boto. [Please follow this link to do it](https://code.google.com/p/boto/wiki/BotoConfig)

And then just run the script from the command line:
```
python awscsecuritygroups.py -h
```

### Notes
You can describe your Security Groups on the same way:
```
[ sg1 ]
vpcid = <vpcid>
description = description sg1
inbound = 
	tcp 22 10.0.1.1/28
	ALL ALL 10.0.1.1/28
	tcp 22 10.0.1.2/28

[ sg2 ]
vpcid = <vpcid>
description = description sg2
inbound = tcp 22 10.0.1.1/28
outbound = tcp 22 10.0.1.1/28
```