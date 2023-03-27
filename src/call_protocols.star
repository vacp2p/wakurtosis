

def send_json_rpc(plan, service_name, port_id, method, params, extract={}):
    recipe = PostHttpRequestRecipe(
        port_id=port_id,
        endpoint="",
        content_type="application/json",
        body='{ "jsonrpc": "2.0", "method": "' + method + '", "params": [' + params + '], "id": 1}',
        extract=extract
    )

    response = plan.wait(recipe=recipe,
                    field="code",
                    assertion="==",
                    target_value=200,
                    service_name=service_name)

    return response


def send_http_get_req(plan, service_name, port_id, endpoint, extract={}):
    recipe = GetHttpRequestRecipe(
        port_id=port_id,
        endpoint=endpoint,
        extract=extract
    )

    response = plan.wait(recipe=recipe,
                    field="code",
                    assertion="==",
                    target_value=200,
                    service_name=service_name)

    return response


def send_http_post_req(plan, service_name, port_id, endpoint, body, extract={}):
    recipe = PostHttpRequestRecipe(
        port_id=port_id,
        endpoint=endpoint,
        content_type="application/json",
        body=body,
        extract=extract
    )

    response = plan.wait(recipe=recipe,
                    field="code",
                    assertion="==",
                    target_value=200,
                    service_name=service_name)

    return response
