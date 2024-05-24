        # # POST METODA TEST
        # endpoint_url = f"{api.url}/films"
        # data_to_post = {'title': 'Example Film', 'director': 'John Doe', 'year': 2024}

        # # TEST: Make a POST request
        # endpoint_url = f"{api.url}/films"
        # data_to_post = {'title': 'Example Film', 'director': 'John Doe', 'year': 2024}
        # post_request = generate_signed_request('POST', endpoint_url, body=json.dumps(data_to_post))
        # core.CfnOutput(self, "POST Request Headers:", value=post_request.headers)


        # # GET Method Test
        # get_endpoint_url = f"{api.url}/films/{response_post['film_id']}"
        
        # def get_request():
        #     response = requests.get(get_endpoint_url)
        #     return response.json()

        # response_get = get_request()
        # get_output = json.dumps(response_get)  # Convert response to JSON string
        # core.CfnOutput(self, "GetResponse", value=get_output)

        # # PUT Method Test
        # put_endpoint_url = f"{api.url}/films/{response_post['film_id']}"
        # data_to_put = {'title': 'Updated Film', 'director': 'Jane Doe', 'year': 2025}

        # def put_request(data):
        #     headers = {'Content-Type': 'application/json'}
        #     response = requests.put(put_endpoint_url, headers=headers, data=json.dumps(data))
        #     return response.json()
        
        # response_put = put_request(data_to_put)
        # put_output = json.dumps(response_put)  # Convert response to JSON string
        # core.CfnOutput(self, "PutResponse", value=put_output)
