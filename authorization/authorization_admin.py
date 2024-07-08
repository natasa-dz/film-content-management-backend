import jwt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def permission_handler(event, context):
    print(event)
    print(event['authorizationToken'])
    # MORAO SAM DA ULAZIM U JWT LOG DA GLEDAM STA VRACA EVENT
    # {'type': 'TOKEN', 'methodArn': 'arn:aws:execute-api:eu-central-1:992382767224:wsjmd4l52g/prod/POST/subscribe', 'authorizationToken': 'Bearer eyJraWQiOiJYR3RZeU12N1wvQ29FQUJYODErWnhPZ1N4dnIwMlQ2RVFqTHc2Mm5sNGx6RT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI3M2E0Mzg1Mi1mMDAxLTcwZjQtNDdiNi1hZmI1NGUxNjMzODMiLCJjb2duaXRvOmdyb3VwcyI6WyJ1c2VyIl0sImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS1jZW50cmFsLTEuYW1hem9uYXdzLmNvbVwvZXUtY2VudHJhbC0xXzBPSW1ORlg3ciIsImNvZ25pdG86dXNlcm5hbWUiOiI3M2E0Mzg1Mi1mMDAxLTcwZjQtNDdiNi1hZmI1NGUxNjMzODMiLCJnaXZlbl9uYW1lIjoiSm9obiIsIm9yaWdpbl9qdGkiOiI4OTUxNmIxOS00NDRhLTRlMjUtYTQ0MS0zYjZlMzhhYWQxMWIiLCJhdWQiOiI3MmtiN3BlaWF1OTByZ2lqZWs0bXNxNmF2NiIsImV2ZW50X2lkIjoiMzU3NjkyMDQtMGFkMy00MGQ1LTgyYTktZTllM2IyOWZmZmNjIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3MjAyMjE5ODQsImV4cCI6MTcyMDIyNTU4NCwiaWF0IjoxNzIwMjIxOTg0LCJmYW1pbHlfbmFtZSI6IkRvZSIsImp0aSI6IjM5YTRjNzU4LTZjNjQtNDEyNS05MjM5LTFiNjM0MDZjZTAxOSIsImVtYWlsIjoicG9wb3ZpYy5zdjQuMjAyMUB1bnMuYWMucnMifQ.oxoGoWnoDLMgyxPbZsUTesQ6XZAASva_dZ9fd4vX-Sfcfne5cxowhCtRjDP190Y5LuTSw0VyQhUFpmP00zviKhjhyIVdUbfH6l7CaedjrHiI06ih5IYjaDpsqTrySHQSVWjJCsVuGibELo8VyZb61meJmPCfqqGaK3a5hy_uaoTRLiEHw0S2to-HIYostmt4cGikCcNKBS7ibrLjoEV-istFAruvJQNToMDM9FyDde4N908njzG0oIbPtEDWCn-Hzax6g9qFmY0gaR1YNvkcZtOrwwE3TdSiADijctjTroVIHxwoaJZH0pVFRJdEL8gGf5A41I9rNmilWrr-NOwZvg'}
    # TOKEN SE MORA SPLIT Bearer eyJraWQiOiJYR3RZeU12N1wvQ... i IMA SPACE IZMEDJU I UZIMAMO 2 VREDNOST, gpt je neke headerse pa sam morao gledati u cloud logs
    # ako budete i vas 2 imali problema mzd da znate
    try:
        token = event['authorizationToken'].split(" ")[1]
        print(token)
        jwt_decode = jwt.decode(token, options={"verify_signature": False})
        print(jwt_decode)
        principal_id = jwt_decode['sub']
        user_groups = jwt_decode.get('cognito:groups', [])
        method_arn = event['methodArn']


        # Provjera dopuštenja na temelju korisničkih grupa
        if 'admin' in [group.lower() for group in user_groups]:
            effect = 'Allow'
        else:
            effect = 'Deny'


        return {
            'principalId': principal_id,
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': method_arn
                }]
            }
        }

    except Exception as e:
        # Ako dođe do bilo kakve greške, vraćamo politiku koja uskraćuje pristup
        return {
            'principalId': 'user',
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Deny',
                    'Resource': event['methodArn']
                }]
            }
        }
