from sto_generator import Generate
import json

def lambda_handler(event, context):
    input = event["body-json"]

    try:
        return {
            'statusCode': 200,
            'generation': Generate(input['Group3s'], input['Fluxes'], input['StartTemps'], input['TempSteps'], input['Exp'], input['idletemps'], input['temperatures'])
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'generation': '',
            'error': str(e)
        }
    #

#
