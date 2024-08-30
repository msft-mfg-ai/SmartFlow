
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

    # Step 1: Email Receipt of Invoice
    email_receipt_res = yield context.call_activity("email_receipt_agent", payload)

    # Step 2: Extraction of Text using OCR Model
    ocr_extraction_res = yield context.call_activity("ocr_extraction_agent", email_receipt_res)

    # Step 3: Analysis of Document using Pre-built Document Intelligence Model
    document_analysis_res = yield context.call_activity("document_analysis_agent", ocr_extraction_res)

    # Step 4: Refinement of Extraction and Mapping into Expected Fields
    extraction_refinement_res = yield context.call_activity("extraction_refinement_agent", document_analysis_res)

    # Step 5-6: Review and Completion Check Loop
    final_refinement_res = yield context.call_sub_orchestrator("review_and_completion_loop", extraction_refinement_res)

    # Step 7: Final Formatting to Ensure Consistency of Extraction Values
    final_formatting_res = yield context.call_activity("final_formatting_agent", final_refinement_res)

    return final_formatting_res

# Sub-Orchestrator for Review and Completion Check Loop
@app.sub_orchestration_trigger(context_name="context")
def review_and_completion_loop(context):
    extraction_refinement_res = context.get_input()

    while True:
        # Step 5: Review Extract to Check for Completeness
        review_res = yield context.call_activity("review_agent", extraction_refinement_res)

        # Step 6: Is Complete?
        completion_check_res = yield context.call_activity("completion_check_agent", review_res)

        if completion_check_res.get("is_complete"):
            return review_res
        else:
            # Loop back to Step 4 for further refinement
            extraction_refinement_res = yield context.call_activity("extraction_refinement_agent", review_res)

# Activities
@app.activity_trigger(input_name="activitypayload")
def email_receipt_agent(activitypayload: str):
    data = json.loads(activitypayload)
    # TO-DO: Add the logic for monitoring the email inbox and retrieving invoices
    return {"invoice_document": "retrieved_invoice.pdf"}

@app.activity_trigger(input_name="activitypayload")
def ocr_extraction_agent(activitypayload: str):
    data = json.loads(activitypayload)
    # TO-DO: Add the logic for extracting text from the invoice document using OCR
    return {"extracted_text": "extracted text from invoice"}

@app.activity_trigger(input_name="activitypayload")
def document_analysis_agent(activitypayload: str):
    data = json.loads(activitypayload)
    # TO-DO: Add the logic for analyzing the extracted text to identify and categorize relevant information
    return {"categorized_data": "categorized and identified data"}

@app.activity_trigger(input_name="activitypayload")
def extraction_refinement_agent(activitypayload: str):
    data = json.loads(activitypayload)
    # TO-DO: Add the logic for refining the extracted data and mapping it into expected fields
    return {"refined_data": "refined and mapped data"}

@app.activity_trigger(input_name="activitypayload")
def review_agent(activitypayload: str):
    data = json.loads(activitypayload)
    # TO-DO: Add the logic for reviewing the refined extract to check for completeness and accuracy
    return {"reviewed_data": "reviewed data"}

@app.activity_trigger(input_name="activitypayload")
def completion_check_agent(activitypayload: str):
    data = json.loads(activitypayload)
    # TO-DO: Add the logic for determining if the data is complete and accurate
    return {"is_complete": True}

@app.activity_trigger(input_name="activitypayload")
def final_formatting_agent(activitypayload: str):
    data = json.loads(activitypayload)
    # TO-DO: Add the logic for performing final formatting to ensure consistency of the extraction values
    return {"formatted_data": "formatted and consistent data"}
