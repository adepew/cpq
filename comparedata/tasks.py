from __future__ import absolute_import
from celery import Celery
import os
import json	
import ast
import requests
import datetime
import time
import sys
import sqlite3
import StringIO
import glob
import traceback
import hashlib

# Celery config
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sfdatacompare.settings')
app = Celery('tasks', broker=os.environ.get('REDIS_URL', 'redis://localhost'))

from django.conf import settings
from comparedata.models import Job, Org, Object, ObjectField, UnmatchedRecord

reload(sys)
sys.setdefaultencoding("utf-8")

@app.task
def get_objects_task(job): 
	"""
		Async method to query objects for the given orgs
	"""

	job.status = 'Downloading Objects'
	job.save()

	# List of standard objects to include
	standard_objects = (
		'Account',
		'AccountContactRole',
		'Asset',
		'Campaign',
		'CampaignMember',
		'Case',
		'CaseContactRole',
		'Contact',
		'ContentVersion',
		'Contract',
		'ContractContactRole',
		'Event',
		'ForecastingAdjustment',
		'ForecastingQuota',
		'Lead',
		'Opportunity',
		'OpportunityCompetitor',
		'OpportunityContactRole',
		'OpportunityLineItem',
		'Order',
		'OrderItem',
		'Pricebook2',
		'PricebookEntry',
		'Product2',
		'Quote',
		'QuoteLineItem',
		'Solution',
		'Task',
		'User',
	)

	# List to determine if exists in other Org
	object_list = []

	# The orgs used for querying
	org_one = job.sorted_orgs()[0]
	org_two = job.sorted_orgs()[1]

	# Describe all sObjects for the 1st org
	org_one_objects = requests.get(
		org_one.instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/sobjects/', 
		headers={
			'Authorization': 'Bearer ' + org_one.access_token, 
			'content-type': 'application/json'
		}
	)

	try:

		# If sobjects exist in the query (should do)
		if 'sobjects' in org_one_objects.json():

			# Iterate over the JSON response
			for sObject in org_one_objects.json()['sobjects']:

				# If the Org is in the standard list, or is a custom object
				if sObject['name'] in standard_objects or sObject['name'].endswith('__c'):

					# Add object to unique list
					object_list.append(sObject['name'])

			org_one.status = 'Finished'

		else:

			org_one.status = 'Error'
			org_one.error = 'There was no objects returned from the query'

	except Exception as error:

		org_one.status = 'Error'
		org_one.error = traceback.format_exc()

	# Now run the process for the 2nd org. Only create object and field records if they exist in both Orgs
	# Describe all sObjects for the 2nd org
	org_two_objects = requests.get(
		org_two.instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/sobjects/', 
		headers={
			'Authorization': 'Bearer ' + org_two.access_token, 
			'content-type': 'application/json'
		}
	)

	try:

		# If sobjects exist in the query (should do)
		if 'sobjects' in org_two_objects.json():

			# Iterate over the JSON response
			for sObject in org_two_objects.json()['sobjects']:

				# If the Org is in the standard list, or is a custom object AND is found in the 1st org
				if (sObject['name'] in standard_objects or sObject['name'].endswith('__c')) and sObject['name'] in object_list:

					# Create object record
					new_object = Object()
					new_object.job = job
					new_object.api_name = sObject['name']
					new_object.label = sObject['label']
					new_object.save()

			org_two.status = 'Finished'

		else:

			org_two.status = 'Error'
			org_two.error = 'There was no objects returned from the query'

	except Exception as error:

		org_two.status = 'Error'
		org_two.error = traceback.format_exc()

	# Save Org 1 and Org 2
	org_one.save()
	org_two.save()

	if org_one.status == 'Error' or org_two.status == 'Error':

		job.status = 'Error'
		job.error = 'There was an error downloading objects and fields for one of the Orgs: \n\n'

		if org_one.error:
			job.error += org_one.error

		if org_two.error:
			job.error += '\n\n' + org_two.error

	else:

		job.status = 'Objects Downloaded'
	
	# Save the job as finished
	job.finished_date = datetime.datetime.now()
	job.save()


@app.task
def compare_data_task(job, object, fields): 
	"""
		Async method to compare the data between selected object and fields
	"""	

	# Update the status
	job.status = 'Comparing Data'
	job.save()

	try:

		# The orgs used for querying
		org_one = job.sorted_orgs()[0]
		org_two = job.sorted_orgs()[1]

		# Set the object against the job
		job.object = object
		job.fields = ', '.join(fields)
		job.object_id = object.id
		job.object_label = object.label
		job.object_name = object.api_name

		# Build the SOQL query
		soql_query = 'SELECT+' + ','.join(fields) + '+FROM+' + object.api_name

		# Query the 1st org
		org_one_records = requests.get(
			org_one.instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/query/?q=' + soql_query, 
			headers={
				'Authorization': 'Bearer ' + org_one.access_token, 
				'content-type': 'application/json'
			}
		)

		if org_one_records.status_code != 200:

			job.status = 'Error'
			job.error = 'There was an error querying records for org one:\n\n' + org_one_records.json()[0]['errorCode'] + ': ' + org_one_records.json()[0]['message'] 

		else:

			# Set the total row count
			job.row_count_org_one = org_one_records.json()['totalSize']

			# Query for the 2nd org
			org_two_records = requests.get(
				org_two.instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/query/?q=' + soql_query, 
				headers={
					'Authorization': 'Bearer ' + org_two.access_token, 
					'content-type': 'application/json'
				}
			)

			if org_two_records.status_code != 200:

				job.status = 'Error'
				job.error = 'There was an error querying records for org two:\n\n' + org_two_records.json()[0]['errorCode'] + ': ' + org_two_records.json()[0]['message'] 

			else:

				# Set the total row count
				job.row_count_org_two = org_two_records.json()['totalSize']

				# List of concatenated fields from the 1st org
				org_one_records_distinct = []
				org_one_records_map = {}

				# Iterate over 1st record
				for record in org_one_records.json()['records']:

					unique_string = ''

					# Iterate over the fields
					for field in fields:
						unique_string += str(record[field])

					# Convert to hash
					unique_string = hash(unique_string)

					# Add the string to the unique list
					org_one_records_distinct.append(unique_string)

					# Add the string to a map of the record
					org_one_records_map[unique_string] = record


				# List of concatenated fields from the 2nd org
				org_two_records_distinct = []
				org_two_records_map = {}

				# Iterate over 2nd record
				for record in org_two_records.json()['records']:

					unique_string = ''

					# Iterate over the fields
					for field in fields:
						unique_string += str(record[field])

					# Convert to hash
					unique_string = hash(unique_string)

					# Add the string to the unique list
					org_two_records_distinct.append(unique_string)

					# Add the string to a map of the record
					org_two_records_map[unique_string] = record

				# Now count matching and unmatching records
				job.matching_rows_count_org_one = 0
				job.matching_rows_count_org_two = 0
				job.unmatching_rows_count_org_one = 0
				job.unmatching_rows_count_org_two = 0

				# Iterate over list one and match against the 2nd list
				for value in org_one_records_distinct:

					# If the row from the 1st list exists in the 2nd list
					if value in org_two_records_distinct:

						# Increment the match count
						job.matching_rows_count_org_one = job.matching_rows_count_org_one + 1

					else:

						# Otherwise increment the non-match count
						job.unmatching_rows_count_org_one = job.unmatching_rows_count_org_one + 1

						# Create a unmatched record
						unmatched_record = UnmatchedRecord()
						unmatched_record.job = job
						unmatched_record.org = org_one

						# Populate the data with the data array
						unmatched_record.data = json.dumps(org_one_records_map[value])

						# Save the record
						unmatched_record.save()

				# Iterate over list two and match against the 1st list
				for value in org_two_records_distinct:

					# If the row from the 2nd list exists in the first list
					if value in org_one_records_distinct:

						# Increment the match count
						job.matching_rows_count_org_two = job.matching_rows_count_org_two + 1

					else:

						# Increment the unmatch count
						job.unmatching_rows_count_org_two = job.unmatching_rows_count_org_two + 1

						# Create a unmatched record
						unmatched_record = UnmatchedRecord()
						unmatched_record.job = job
						unmatched_record.org = org_two

						# Populate the data with the data array
						unmatched_record.data = json.dumps(org_two_records_map[value])

						# Save the record
						unmatched_record.save()

				# Set the status to finished
				job.status = 'Finished'

	except:

		job.status = 'Error'
		job.error = traceback.format_exc()

	# Save the job
	job.save()
