# Example file to demonstrate local lambda function testing

import lambda_function as lam

result = lam.lambda_handler({
    'control': {
        'machine': 'Maintenance',
        'fields': [
            {
                'name': 'record',
                'table': 'Records',
                'type': 'single',
                'independent': True,
                'master': True
            }, {
                'name': 'sources',
                'table': 'Sources',
                'type': 'list',
                'independent': False,
                'master': False
            }
        ]
    },
    'params': {
        'querystring': {
        },
        'path': {
        }
    },
    'body-json': {
	    "record": {
		    "system": "Echo",
		    "recorder": "Jill",
		    "date": "",
		    "p1": "",
		    "p2": "",
		    "summary": "",
		    "issues": "",
		    "future": "",
		    "notes": ""
	    },
	    "sources": []
    }
}, None)
print result
