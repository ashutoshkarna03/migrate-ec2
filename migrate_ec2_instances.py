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

# function to get status of the given instance id
def get_instance_status(instance_id, client):
    response = client.describe_instances(
        InstanceIds=[
            instance_id,
        ],
    )
    state = response['Reservations'][0]['Instances'][0]['State']['Name']
    return state
 
def stop_instance(instance_id, client):
    waiter = client.get_waiter('instance_stopped')
    # call stop_instances to stop the instance 
    response = client.stop_instances(InstanceIds=[instance_id], DryRun=False)
    # waiter waits until the stop operation is complete
    waiter.wait(InstanceIds=[instance_id,], DryRun=False)
    return dict(success=True)

def create_image_of_instance(instance_id, client):
    waiter = client.get_waiter('image_available')
    # call create_image to create AMI of given instance
    response = client.create_image(InstanceId=instance_id, Name="Latest-image-of-" + instance_id)
    pprint(response)
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
    waiter.wait(ImageIds=[new_image_id], DryRun=False)
    return new_image_id
    




if __name__ == '__main__':
    # print(get_instance_status('i-0158c9fa71e43d137'))
    image_id = 'ami-0aab5b8c501dd81e0'
    instance_id = 'i-0258ceb7c8aed1e08'
    # print(create_image_of_instance('i-0258ceb7c8aed1e08', client_des))
    print(copy_image_to_destination_region(image_id, instance_id, client_des))
