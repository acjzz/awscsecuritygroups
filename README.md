## AWScSecurityGroups stands for *AWS Cloud SecurityGroups*

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
Please check the [example.conf](example.conf) file