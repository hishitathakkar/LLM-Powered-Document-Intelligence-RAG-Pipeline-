def parse_pdf(parser, **kwargs):
    pdf_path = kwargs['ti'].xcom_pull(key='pdf_path')
    print(f"Parsing PDF using: {parser}")
    
    if parser == 'docling':
        parsed_text = f"Parsed with Docling from {pdf_path}"
    elif parser == 'mistral_ocr':
        parsed_text = f"OCR text from {pdf_path}"
    else:
        raise ValueError("Unsupported parser")
    
    kwargs['ti'].xcom_push(key='parsed_text', value=parsed_text)
