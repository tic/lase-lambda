from pymysql import escape_string as esc

if __name__ == '__main__':
    print 'This file should be imported, not directly executed.'

def FilteredQuery(table, select=['*'], filters={}):
	# Create first part of the sql query
	q = FilterlessQuery(table, select=select)

	# If an empty filter was given, just return now
	if len(filters) == 0:
		return q

	# For each value in the filter, add it to the array of criteria and add string markers if needed
	criteria = []
	for key in filters:
		if key == 'days':
			criterion = 'timestamp >= DATE_ADD(CURDATE(), interval -{} day)'.format(esc(filters[key]))
		elif key == 'mindate':
			criterion = 'Date >= \'{}\''.format(esc(filters[key]))
		elif key == 'maxdate':
			criterion = 'Date <= \'{}\''.format(esc(filters[key]))
		elif key == 'keywords':
			kws = [esc(kw) for kw in filters[key].split(' ')]
			if table == 'growths':
				crits = ['(Description like \'%{}%\')'.format(kw) for kw in kws]
			else:
				crits = ['(author like \'%{}%\' or title like \'%{}%\')'.format(kw, kw) for kw in kws]
			criterion = ' and '.join(crits)
			criterion = '({})'.format(criterion)
		else:
			criterion = "{}='{}'".format(esc(key), esc(filters[key]))
		criteria.append(criterion)

	# Join criteria together with sql and's
	criteria = ' and '.join(criteria)

	# Generate the final query with the where keyword
	return '{} where {}'.format(q, criteria)
#

def FilterlessQuery(table, select=['*']):
	ret = 'select {} from {}'
	selections = esc(','.join(select))
	return ret.format(selections, esc(table))
#

def PaginateQuery(query, page_size=100, page_number=0, sortby='id', reverse=False):
	skip = page_size * page_number
	return '{} order by {} {} limit {}, {}'.format(query, sortby, 'desc' if reverse else 'asc', skip, page_size)
#

def DeleteQuery(table, id=-1, param='id'):
	try:
		id = int(id)
	except ValueError:
		id = -1
	return 'delete from {} where {}={}'.format(esc(table), esc(param), id)
#

def InsertQuery(table, fields={}):
	# fields: {'column_name': 'column_value', ...}
	columns = []
	values = []
	for key in fields:
		columns.append(key)
		val = fields[key]
		if isinstance(val, basestring):
			val = "'{}'".format(esc(val))
		values.append(str(val))
	return 'insert into {} ({}) values ({})'.format(esc(table), ', '.join(columns), ', '.join(values))
#
