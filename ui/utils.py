import fitz  # PyMuPDF
import re


def extract_mcqs_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    
    # Extract text from ALL pages
    all_text = ""
    page_count = len(doc)
    
    for page_num in range(page_count):
        page = doc[page_num]
        page_text = page.get_text()
        all_text += page_text + "\n\n"  # Add spacing between pages
    
    doc.close()  # Close the document to free memory
    
    mcqs = []
    
    # Split text by question numbers to isolate each question block
    question_blocks = re.split(r'(?=^\s*\d+\s*\.)', all_text, flags=re.MULTILINE)
    
    # Remove empty blocks
    question_blocks = [block.strip() for block in question_blocks if block.strip()]
    
    # Now try to extract MCQs from each block individually
    for i, block in enumerate(question_blocks):
        if not block.strip():
            continue
            
        # Try multiple patterns on each block
        patterns = [
            # Simple pattern for individual blocks
            r'^(\d+)\s*\.\s*(.*?)\s*A[.)]\s*(.*?)\s*B[.)]\s*(.*?)\s*C[.)]\s*(.*?)\s*D[.)]\s*(.*?)\s*(?:Answer|Ans|ANS)[:\s]*([A-D])',
            
            # Pattern with more flexible spacing
            r'(\d+)\s*\.\s*(.*?)(?:\n|\s+)A[.)]\s*(.*?)(?:\n|\s+)B[.)]\s*(.*?)(?:\n|\s+)C[.)]\s*(.*?)(?:\n|\s+)D[.)]\s*(.*?)(?:\n|\s+)(?:Answer|Ans|ANS)[:\s]*([A-D])',
            
            # Pattern handling line breaks
            r'(\d+)\s*\.\s*((?:(?!A[.)]).*?)*)\s*A[.)]\s*((?:(?!B[.)]).*?)*)\s*B[.)]\s*((?:(?!C[.)]).*?)*)\s*C[.)]\s*((?:(?!D[.)]).*?)*)\s*D[.)]\s*((?:(?!(?:Answer|Ans)).*?)*)\s*(?:Answer|Ans|ANS)[:\s]*([A-D])'
        ]
        
        for j, pattern in enumerate(patterns):
            matches = re.findall(pattern, block, re.DOTALL | re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    if len(match) >= 7:
                        question_num, question, a, b, c, d, ans = match[:7]
                        
                        # Clean up text
                        question = re.sub(r'\s+', ' ', question.strip())
                        a = re.sub(r'\s+', ' ', a.strip())
                        b = re.sub(r'\s+', ' ', b.strip())
                        c = re.sub(r'\s+', ' ', c.strip())
                        d = re.sub(r'\s+', ' ', d.strip())
                        
                        # Skip if any field is empty
                        if not all([question, a, b, c, d, ans]):
                            continue
                        
                        mcqs.append({
                            "question": question,
                            "option_a": a,
                            "option_b": b,
                            "option_c": c,
                            "option_d": d,
                            "correct_answer": ans.strip().upper()
                        })
                break
    
    return mcqs




