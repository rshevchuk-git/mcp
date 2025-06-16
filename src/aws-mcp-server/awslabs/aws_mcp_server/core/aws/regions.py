# These global services don't have regionalized endpoints
NON_REGIONALIZED_SERVICES = ('iam', 'route53')

# These global services have fixed regionalized endpoints
GLOBAL_SERVICE_REGIONS = {
    'devicefarm': 'us-west-2',
    'ecr-public': 'us-east-1',
    'globalaccelerator': 'us-west-2',
    'marketplace-catalog': 'us-east-1',
    'route53-recovery-control-config': 'us-west-2',
    'route53-recovery-readiness': 'us-west-2',
    'route53domains': 'us-east-1',
    'sagemaker-geospatial': 'us-west-2',
}
