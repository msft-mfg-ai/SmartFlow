import azure.functions as func
import azure.durable_functions as df
import logging
import json
import os

app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)

# An HTTP-Triggered Function with a Durable Functions Client binding
@app.route(route="orchestrators/{functionName}")
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client):
    function_name = req.route_params.get('functionName')
    payload = json.loads(req.get_body())
    instance_id = await client.start_new(function_name, client_input=payload)
    response = client.create_check_status_response(req, instance_id)
    return response

# Orchestrator
@app.orchestration_trigger(context_name="context")
def agent_orchestrator(context):

    # Get the input payload from the context
    payload = context.get_input()

    arg1 = payload.get("arg1")
    arg2 = payload.get("arg2")

    agent_1_res = yield context.call_activity("agent_1", json.dumps({"arg1": arg1}))
    agent_2_res = yield context.call_activity("agent_2", json.dumps({"arg2": arg2, "result": agent_1_res}))
   
    return agent_2_res

# Activities
@app.activity_trigger(input_name="activitypayload")
def agent_1(activitypayload: str):

    # Load the activity payload as a JSON string
    data = json.loads(activitypayload)

    # TO-DO: Add the logic for the activity function
    return None
    

@app.activity_trigger(input_name="activitypayload")
def agent_2(activitypayload: str):

    # Load the activity payload as a JSON string
    data = json.loads(activitypayload)

    # TO-DO: Add the logic for the activity function
    return None
    
