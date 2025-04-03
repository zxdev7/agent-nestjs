import streamlit as st
import requests
import json

# UI
st.title("OpenAPI 3.0.0 JSON to Prompt Generator")

# Input Token
token = st.text_input("Bearer Token:", type="password")

# Input Base URL
base_url = st.text_input("Base URL:")

# Import OpenAPI JSON
option = st.radio("OpenAPI JSON Input Method:", ["Upload File", "Import from URL"])

openapi_json = None

if option == "Upload File":
    uploaded_file = st.file_uploader("Choose an OpenAPI JSON file", type="json")
    if uploaded_file:
        openapi_json = json.load(uploaded_file)
elif option == "Import from URL":
    url = st.text_input("Enter OpenAPI JSON URL:")
    if url:
        response = requests.get(url)
        if response.status_code == 200:
            openapi_json = response.json()
        else:
            st.error("Failed to fetch JSON")

all_prompts = ""

# Helper function to resolve $ref

def resolve_ref(ref, openapi_json):
    parts = ref.strip('#/').split('/')
    ref_obj = openapi_json
    for part in parts:
        ref_obj = ref_obj.get(part, {})
    return ref_obj

if openapi_json and base_url:
    paths = openapi_json.get("paths", {})

    if st.button("Generate and Test All APIs"):
        for path, methods in paths.items():
            for method, api_details in methods.items():
                full_url = f"{base_url}{path}"
                headers = {"Authorization": f"Bearer {token}"}
                request_body_info = "ไม่มี request body"

                if "requestBody" in api_details:
                    content = api_details["requestBody"].get("content", {})
                    if "application/json" in content:
                        schema = content["application/json"].get("schema", {})
                        if "$ref" in schema:
                            schema = resolve_ref(schema["$ref"], openapi_json)
                        request_body_info = f"เป็น json: {json.dumps(schema, indent=2, ensure_ascii=False)}"
                    elif "multipart/form-data" in content:
                        schema = content["multipart/form-data"].get("schema", {})
                        if "$ref" in schema:
                            schema = resolve_ref(schema["$ref"], openapi_json)
                        request_body_info = f"เป็น form data: {json.dumps(schema, indent=2, ensure_ascii=False)}"

                try:
                    test_response = requests.request(method.upper(), full_url, headers=headers)
                    response_json = test_response.json()
                except Exception:
                    response_json = test_response.text

                prompt = f"""
[{api_details.get('summary', 'No description provided')}]
{{API_URL}}{path} {method.upper()}
Authorization: Bearer {{token}}
request body {request_body_info}
response: {json.dumps(response_json, indent=2, ensure_ascii=False)}
"""
                all_prompts += prompt + "\n\n"

                st.subheader(f"API: {method.upper()} {path}")
                st.text_area("Generated Prompt", prompt, height=300)
                st.json(response_json)

        st.download_button("Export All Prompts as TXT", data=all_prompts, file_name="api_prompts.txt")
