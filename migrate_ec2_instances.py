import boto3
from botocore.exceptions import ClientError
import dotenv
import os
from pprint import pprint

# load environment variables
dotenv.load_dotenv()  # by default it takes .env file

# create boto3 client for ec2 for both source and destination region
client_src = boto3.client('ec2', region_name=os.getenv('SOURCE_REGION'))
client_des = boto3.client('ec2', region_name=os.getenv('DESTINATION_REGION'))
# create ec2 resource
ec2 = boto3.resource('ec2', region_name=os.getenv('DESTINATION_REGION'))

# function to get status of the given instance id
def get_instance_details(instance_id, client):
    response = client.describe_instances(
        InstanceIds=[
            instance_id,
        ],
    )
    return dict(
        instance_type = response['Reservations'][0]['Instances'][0]['InstanceType'],
        state = response['Reservations'][0]['Instances'][0]['State']['Name'],
    )
     
def stop_instance(instance_id, client):
    waiter = client.get_waiter('instance_stopped')
    # call stop_instances to stop the instance 
    response = client.stop_instances(InstanceIds=[instance_id], DryRun=False)
    # waiter waits until the stop operation is complete
    print('Stopping instance, this may take few minutes...')
    waiter.wait(InstanceIds=[instance_id,], DryRun=False)
    return dict(success=True)

def create_image_of_instance(instance_id, client):
    waiter = client.get_waiter('image_available')
    # call create_image to create AMI of given instance
    response = client.create_image(InstanceId=instance_id, Name="Latest-image-of-" + instance_id)
    print('Creating image, this may take few minutes...')
    waiter.wait(ImageIds=[response['ImageId']], DryRun=False)
    return response['ImageId']

def copy_image_to_destination_region(image_id, instance_id, client):
    waiter = client.get_waiter('image_available')
    source_region = os.getenv('SOURCE_REGION')
    # call copy_image to copy the AMI from source region to destination
    response = client.copy_image(
        Description='copied image of instance: ' + instance_id + ' from region: ' + source_region,
        Name='New image of instance ' + instance_id,
        SourceImageId=image_id,
        SourceRegion=source_region,
    )
    new_image_id = response['ImageId']
    print('Copying image, this may take few minutes...')
    waiter.wait(ImageIds=[new_image_id], DryRun=False)
    return new_image_id

def launch_instance(image_id, instance_id, client_src, client_des, ec2_resource_des):
    # create waiter for destination instance to check if instance status is `ok`
    waiter = client_des.get_waiter('instance_status_ok')
    # get the source instance details needed for launching the instance
    instance_detail = get_instance_details(instance_id, client_src)
    # launch instance using create_instances() method of ec2 resource
    try:
        response = ec2_resource_des.create_instances(
            ImageId=image_id,
            InstanceType=instance_detail['instance_type'],
            MaxCount=1,
            MinCount=1,
            DryRun=False,
            Monitoring={'Enabled': False},
        )
        instance_id = str(response[0]).split("'")[1]
        print('Creating instance, this may take few minutes...')
        waiter.wait(InstanceIds=[instance_id], DryRun=False)
        return dict(success=True)
    except Exception as e:
        print('Error in launching intance with error: ' + str(e))
        return dict(success=False, error_msg=str(e))
    
    




if __name__ == '__main__':
    # print(get_instance_details('i-0258ceb7c8aed1e08', client_src))
    image_id = 'ami-07aa3df10dae9a6b9'
    # instance_id = 'i-0258ceb7c8aed1e08'
    # print(create_image_of_instance('i-0258ceb7c8aed1e08', client_des))
    # print(copy_image_to_destination_region(image_id, instance_id, client_des))
    launch_instance(
        instance_id='i-0258ceb7c8aed1e08',
        image_id='ami-07aa3df10dae9a6b9',
        client_src=client_src,
        client_des=client_des,
        ec2_resource_des=ec2
    )
