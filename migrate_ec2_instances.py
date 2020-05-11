import boto3
import dotenv
from pprint import pprint

# load environment variables
dotenv.load_dotenv()  # by default it takes .env file

# create boto3 client for ec2
client = boto3.client('ec2')


