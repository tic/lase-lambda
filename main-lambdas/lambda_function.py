# Written for Python 2.7

from pymysql import connect, escape_string as esc
from QueryManager import FilteredQuery, PaginateQuery, DeleteQuery, InsertQuery
from ObjectConverter import fMap
from errors import FailedConnection, InvalidInput
from keys import url as connection_url, user as connection_user, passwd as connection_passwd

# Returns two element tuple containing the selected
# db and whether growths are involved.
def set_db(cnx, requested):
	if requested == 'Bravo':
		cnx.select_db('Bravo')
		return ('Bravo', True)
	elif requested == 'Maintenance':
		cnx.select_db('Maintenance')
		return ('Maintenance', False)
	elif requested == 'Publications':
		cnx.select_db('Publications')
		return ('Publications', False)
	elif requested == 'Wafers':
		cnx.select_db('Wafers')
		return ('Wafers', False)
	elif requested == 'Settings':
		cnx.select_db('Settings')
		return ('Settings', False)
	else: # Use Echo machine by default
		cnx.select_db('Echo')
		return ('Echo', True)
#

# Relies on control schema from Lambda mapping template:
# control: {
# 	'machine': 'user_given',
# 	'select': {
# 		... column names, if applicable ...
# 	},
# 	'returnKey': 'abc123',
# 	'source': 'fromMachineGrowth',
# 	'pathParams': []
# }
def lambda_handler(event, context):
	try:
		cnx = connect(connection_url, user=connection_user,
						   passwd=connection_passwd, connect_timeout=5)
	except:
		return FailedConnection

	try:
		# ###############################
		# ###############################
		# 			Get handler
		# ###############################
		# ###############################
		if event['control']['method'] == 'GET':
		    # Pull desired table, set db connection, and set item sort direction
			table = esc(event['control']['table'])
			selected_db, is_growth = set_db(cnx, event['params']['path']['machine']) if event['control']['machine'] == 'user_given' else set_db(cnx, event['control']['machine'])
			reverse = True if selected_db == 'Wafers' or is_growth else False

			try: # Try to parse a page number from the query
				page = int(event['params']['querystring']['page'])
				del event['params']['querystring']['page']
			except: # Default page is page 0 (the first one)
				page = 0

			try: # Some queries select only certain fields.
				select = event['control']['select']
			except: # Default is select all
				select=['*']

		    # Combine query and path filters
			filters = event['params']['querystring'] if event['control']['queryFilters'] else {}
			for key in event['control']['pathParams']:
				filters[key] = event['params']['path'][key]

		    # Start by creating a filtered query, then make it paginated
			q = PaginateQuery(FilteredQuery(table, select=select, filters=filters), page_number=page, record=table == 'Records', reverse=reverse)
			data = []

		    # Consult with sql backend
		    try:
		        with cnx.cursor() as cur:
					cur.execute(q)
					if event['control']['singleItem']:
						data = fMap[event['control']['source']](cur.fetchone())
					else:
						data = [fMap[event['control']['source']](arr) for arr in cur]
		    except Exception as e:
		        return InvalidInput

			return { # Pass data back to client
				'statusCode': 200,
				event['control']['returnKey']: data,
			}

		# ###############################
		# ###############################
		# 		Delete handler
		# ###############################
		# ###############################
		if event['control']['method'] == 'DELETE':
			table = esc(event['control']['table'])
			selected_db, _ = set_db(cnx, event['params']['path']['machine']) if event['control']['machine'] == 'user_given' else set_db(cnx, event['control']['machine'])

			key = event['control']['key']
			q = DeleteQuery(table, param=key, id=event['params']['path'][key])

			try:
				with machine.cursor() as cur:
					cur.execute(q)
				machine.commit()
			except Exception as e:
				machine.rollback()
				return {
					'statusCode': 422,
					'message': 'Verify the following, as applicable: querystrings are valid keys for filtering the requested data; parameters are valid.'
				}
			# Pass data back to client
			return {
				'statusCode': 200,
				'message': 'Success',
			}

		# ###############################
		# ###############################
		# 			Put handler
		# ###############################
		# ###############################
		if event['control']['method'] == 'PUT':
			selected_db, _ = set_db(cnx, event['params']['path']['machine']) if event['control']['machine'] == 'user_given' else set_db(cnx, event['control']['machine'])
			q = ''
			try:
				body = event['body-json']
				transaction_log = []
				last_fk = 0
				master_id = -1
				with cnx.cursor() as cur:
					for field in event['control']['fields']:
						table = esc(field['table'])

						if field['type'] == 'single':
							insert_fields = body[field['name']]
							if not field['independent']:
								insert_fields[field['link_fk']] = last_fk
							q = InsertQuery(table, fields=insert_fields)
							cur.execute(q)
							transaction_log.append({'table': table, 'id': cur.lastrowid})

							if field['master']:
								master_id = cur.lastrowid
							if field['independent']:
								last_fk = cur.lastrowid

						elif field['type'] == 'list':
							for insert_fields in body[field['name']]:
								if not field['independent']:
									insert_fields[field['link_fk']] = last_fk

								cur.execute(InsertQuery(table, fields=insert_fields))
								transaction_log.append({'table': table, 'id': cur.lastrowid})

								if field['independent']:
									last_fk = cur.lastrowid
				print "Transactions finished, committing"
			except Exception as err:
				print err
				print "Transactions failed. Removing previously inserted rows."
				with cnx.cursor() as cur:
					for entry in transaction_log:
						cur.execute(DeleteQuery(entry['table'], id=entry['id']))
				return {
					'statusCode': 422,
					'message': 'Expected schema must be followed tightly. Invalid column names, unexpected objects or lists, etc. cannot be provided for PUT requests.',
					'err': str(err),
					'q': q
				}
			finally:
				cnx.commit()

			# Pass data back to client
			return {
				'statusCode': 200,
				'id': master_id,
			}
	finally:
		print 'Closing internal connection'
		cnx.close()

#
