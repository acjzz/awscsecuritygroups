#!/usr/bin/python
import ansible.runner
import ConfigParser
from troposphere import Template, Ref
import troposphere.ec2 as ec2
import re
import time
import logging
import argparse
import os


SCRIPT_NAME = 'AWScSecurityGroups'

logger = logging.getLogger(SCRIPT_NAME)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

if not os.path.exists('logs'):
    os.makedirs('logs') 

if not os.path.exists('tmp'):
    os.makedirs('tmp') 

fh = logging.FileHandler('logs/awscsecuritygroups.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)

class SecurityGroups():

    @staticmethod
    def sanitize(basestring):
        return basestring.strip(' \n\t\r').split(' ')

    @staticmethod
    def parseRule(rule):
        rproto = '([a-z]+)'
        rport = '(([0-9]+)|([al]+))'
        rcidr = '([0-9]+.[0-9]+.[0-9]+.[0-9]+/[0-9]+)'
        rspace = '\s+'
        rsecgroup = '([a-z\-_]+)'
        rsecgroupid = '(sg-[0-9a-z]+)'

        for regex in [ rproto + rspace + rport + rspace + rsecgroupid,
                       rproto + rspace + rport + '-' + rport + rspace + rsecgroupid,
                       rproto + rspace + rport + rspace + rsecgroup,
                       rproto + rspace + rport + '-' + rport + rspace + rsecgroup,
                       rproto + rspace + rport + rspace + rcidr,
                       rproto + rspace + rport + '-' + rport + rspace + rcidr,
                    ]:

            matches = re.compile(regex, re.IGNORECASE).findall(rule)

            if len(matches):
                matches[0] = filter(None, matches[0])
                result = {}
                result['IpProtocol'] = matches[0][0]
                result['FromPort'] = matches[0][1]
                result['ToPort'] = matches[0][-2]

                if result.get('IpProtocol').lower() == "all":
                     result['IpProtocol'] = "-1"

                if result.get('FromPort').lower() == "all":
                    result['FromPort'] = "0"
                    result['ToPort'] = "65535"

                if re.compile(rcidr, re.IGNORECASE ).findall(matches[0][-1]):
                    result['CidrIp'] = matches[0][-1]
                elif re.compile(rsecgroupid, re.IGNORECASE ).findall(matches[0][-1]):                    
                    result['SourceSecurityGroupId'] = Ref(matches[0][-1])
                else:
                    result['SourceSecurityGroupName'] = Ref(matches[0][-1])

                return ec2.SecurityGroupRule('',**result) 

    def __init__(self, environment, stack_description):
        self.data = {}
        self.config = ConfigParser.ConfigParser()
        created = time.strftime( "%Y-%m-%d %H:%M:%S" )
        self.DefaultsTags = [ ec2.Tag( "Environment" , environment ) , ec2.Tag( "Created" ,  created ) ]
        self.stack_description = stack_description

    def read(self, filename):
        self.config.read( filename )
        for section in self.config.sections():
            self.data[section] = { 'SecurityGroupIngress':[],'SecurityGroupEgress':[]}
            self.data.get(section)['VpcId'] = self.config.get(section,'vpcid')
            self.data.get(section)['GroupDescription'] = self.config.get(section,'description')
            for x,y in [('inbound', "SecurityGroupIngress"), ('outbound',"SecurityGroupEgress")]: 
                if self.config.has_option(section, x):
                    for rule in self.config.get(section, x ).split('\n'):
                        if rule:
                            self.data.get(section).get( y ).append(self.parseRule(rule))

    def _getTemplateElements(self):
        for secg in self.data.keys():
            data = self.data.get(secg)
            data["Tags"] = [ ec2.Tag('Name', secg) ] + self.DefaultsTags
            yield ec2.SecurityGroup( secg.strip() , **data )

    def create(self):
        template = Template()
        template.add_description( self.stack_description )
        for el in self._getTemplateElements():
            template.add_resource(el)
        return template


def create_stack(stack_name,template_name, region="eu-west-1", disable_rollback="no"):
    logger.info("Creating template %s"%template_name)
    hosts = [ '127.0.0.1' ]
    inventory = ansible.inventory.Inventory(hosts)

    results = ansible.runner.Runner(
        module_name='cloudformation', 
        module_args='stack_name="%s" state=present region=%s disable_rollback=%s template=%s'%(stack_name,region,disable_rollback,template_name),
        pattern="*",
        inventory=inventory,
        transport='local'
        ).run()

    if results is None:
       print "No hosts found"
       sys.exit(1)

    for (hostname, result) in results['contacted'].items():
        if "failed" in result.keys() and result["failed"]:
            print "Failed:"
            print result
        elif "changed" in result.keys():
            print "Changed"
            print result["output"]
        else:
            print hostname,result
def main():
    regions = ['us-east-1','us-east-2','us-west-1','eu-west-1','ap-southeast-1','ap-southeast-2','ap-northeast-1','sa-east-1']

    parser = argparse.ArgumentParser()
    

    parser.add_argument('-s', '--stack', 
                        help='Stack name',
                        required=True)
    parser.add_argument('-e', '--environment', 
                        help='Environment name',
                        required=True)
    parser.add_argument('-f', '--securitygroups_file', 
                        help='Config File of security groups specification',
                        required=True)
    parser.add_argument('-r', '--region', 
                        choices= regions,
                        default='eu-west-1')

    args = parser.parse_args()

    logger.info('Executing %s'%args)
    logger.info('Creating cloudformation template')

    sgp = SecurityGroups("%s::SecurityGroups"%args.environment, "%s::SecurityGroups"%args.environment)
    sgp.read(args.securitygroups_file)
    template = sgp.create()
    f = open(os.path.join("tmp","cloudformation"),'w')
    f.write(template.to_json())
    f.close()
    logger.info('Creating Stack: %s'%args.stack)
    create_stack(args.stack,os.path.join("tmp","cloudformation"), region=args.region, disable_rollback="no")

if __name__ == '__main__':
    main()





