# Written for Python 2.7

from pymysql import connect, escape_string as esc
from QueryManager import FilteredQuery, PaginateQuery
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
    finally:
        cnx.close()

	return { # Pass data back to client
		'statusCode': 200,
		event['control']['returnKey']: data,
	}


#
