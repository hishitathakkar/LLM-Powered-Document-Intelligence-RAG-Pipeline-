import streamlit as st
import requests


# Set FastAPI URL
API_BASE_URL = "http://127.0.0.1:8000"


st.title("PDF AI Assistant with RAG")

st.divider()

st.sidebar.title("Navigation")
page = st.sidebar.radio("Services", ["File and RAG Method Selection", "LLM Interaction"])

if 'selected_year' not in st.session_state:
    st.session_state.selected_year = ""

if 'selected_quarter' not in st.session_state:
    st.session_state.selected_quarter = ""


if page == "File and RAG Method Selection":

    st.subheader("Select an Input Source")

    input_source = st.selectbox('Upload a New PDF or Use NVIDIA Reports', ["Upload a New PDF", "Use the NVIDIA quarterly reports PDFs"])

    st.divider()

    if input_source == "Upload a New PDF":

        st.subheader("Upload a New PDF")


        uploaded_file = st.file_uploader("Choose a PDF File", type="pdf")

        if st.button("Upload PDF File"):

            if uploaded_file:
                st.info("Uploading PDF for processing...")
                files = {"file": uploaded_file}

                try:
                    response = requests.post(f"{API_BASE_URL}/upload_pdf", files=files)

                    if response.status_code == 200:
                        st.success("File uploaded and parsed successfully!")
                    else:
                        st.error(f"Error: {response.json()['detail']}")

                except Exception as e:
                    st.error(f"Error during PDF upload: {str(e)}")


        col1, col2, col3 = st.columns(3)

        with col1:
            parser_options = ["Docling", "Mistral OCR"]
            selected_parser = st.selectbox("Select a PDF Parser", parser_options, index=0)

            params = {"selected_parser": selected_parser}
            response = requests.get(f"{API_BASE_URL}/pdf_parser", params=params)

        with col2:
            chunking_options = [" Token-Based Chunking", "Recursive Character/Token Chunking", "Semantic Chunking (Kamradt Method)"]
            selected_chunk = st.selectbox("Select a Chunking Strategy", chunking_options, index=0)

            params = {"selected_chunk": selected_chunk}
            response = requests.get(f"{API_BASE_URL}/chunking_strat", params=params)


        with col3:
            quarter = ["Q1", "Q2", "Q3", "Q4"]
            quarters = st.selectbox("Select required Quarters", quarter)
            rag_method = ["Pinecone", "ChromaDB"]
            selected_rag = st.selectbox("Select a RAG Method", rag_method, index=0)


            params = {"selected_rag": selected_rag, "quarters": quarters}
            response = requests.get(f"{API_BASE_URL}/rag_method", params=params)



    elif input_source == "Use the NVIDIA quarterly reports PDFs":
        
        st.subheader("Select Year and Quarter of Parsed PDFs")


        col1, col2 = st.columns(2)

       # with col1:
           # st.session_state.selected_year = ""
           # year = ["2020", "2021", "2022", "2023", "2024"]
            #selected_year = st.multiselect("Select required Years", year)
            #st.session_state.selected_year = selected_year

        with col2:
            st.session_state.selected_quarter = ""
            quarters = ["Q1", "Q2", "Q3", "Q4"]
            selected_quarter = st.multiselect("Select required Quarters", quarters)
            st.session_state.selected_quarter = selected_quarter 

else:
    st.subheader("Responses for Questions on Documents")

    question = st.text_input("Ask a question about the document")

    if st.button("Get a Response") and question:

        params = {"question": question, "selected_quarter": st.session_state.selected_quarter, "selected_rag":st.session_state.selected_rag}
        response = requests.get(f"{API_BASE_URL}/ask_question", params=params)

        st.write(response.json()['choices'][0]['message']['content'])

        input_tokens = response.json()['usage']['prompt_tokens']
        output_tokens = response.json()['usage']['completion_tokens']
    
        param = {'input_tokens': input_tokens, 'output_tokens': output_tokens}
        response = requests.get(f"{API_BASE_URL}/pricing", params=param)
    
        total = response.json().get('total_value')

        st.divider()
    
        st.write(f'Total Input Tokens: {input_tokens}')
        st.write(f'Total Output Tokens: {output_tokens}')
        st.write(f'Total Price of this Query: ${total}') 