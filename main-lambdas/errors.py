if __name__ == '__main__':
    print 'This file should be imported, not directly executed.'

FailedConnection = {
    'statusCode': 500,
    'message': 'failed to establish internal connection'
}

InvalidInput = {
    'statusCode': 422,
    'message': 'Verify the following, as applicable: querystrings are valid keys for filtering the requested data; parameters are valid.'
}
