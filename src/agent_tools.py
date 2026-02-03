from langchain_classic.tools import Tool, tool
from langchain_community.tools import DuckDuckGoSearchRun
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
import os

# --- TOOL 1: THE WORD PROCESSOR ---
@tool
def create_word_document(content: str):
    """
    Useful for creating Word documents. 
    Input should be the raw text content.
    """
    try:
        doc = Document()
        
        # Global Font Settings
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(14)
        style.paragraph_format.space_after = Pt(0) 

        lines = content.split('\n')
        header_paragraph = None

        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                if header_paragraph: header_paragraph = None
                doc.add_paragraph() 
                continue

            lower_line = clean_line.lower()

            # Removal Logic
            if "memorandum" in lower_line or "dress code:" == lower_line or "wifi access:" == lower_line:
                continue

            # Header Logic (To/From/Date)
            if lower_line.startswith(("to:", "from:", "date:")):
                if header_paragraph is None:
                    header_paragraph = doc.add_paragraph()
                else:
                    header_paragraph.add_run().add_break()
                
                if ":" in clean_line:
                    prefix, value = clean_line.split(":", 1)
                    run = header_paragraph.add_run(prefix + ":")
                    run.bold = True
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(14)
                    run_val = header_paragraph.add_run(value)
                    run_val.font.name = 'Times New Roman'
                    run_val.font.size = Pt(14)
                else:
                    run = header_paragraph.add_run(clean_line)
                    run.bold = True

            # Subject Line Logic
            elif lower_line.startswith("subject:"):
                header_paragraph = None 
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(clean_line)
                run.bold = True
                run.font.name = 'Times New Roman'
                run.font.size = Pt(14)

            # Signature Logic
            elif lower_line.startswith(("sincerely", "[your name", "[company")):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                run = p.add_run(clean_line)
                run.font.name = 'Times New Roman'
                run.font.size = Pt(14)

            # Body Text Logic
            else:
                header_paragraph = None 
                p = doc.add_paragraph()
                parts = clean_line.split('**')
                for i, part in enumerate(parts):
                    run = p.add_run(part)
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(14)
                    if i % 2 == 1: run.bold = True

        save_dir = r"E:\New folder\Agentic Ai\Intern Agent\data"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        filename = os.path.join(save_dir, "agent_output_v2.docx")
        doc.save(filename)
        return f"Successfully created Polished Document: {filename}"

    except Exception as e:
        return f"Error creating document: {str(e)}"

# --- TOOL 2: WEB SEARCH ---
def get_search_tool():
    return Tool(
        name="web_search",
        func=DuckDuckGoSearchRun().run,
        description="Useful for searching the internet for current events or tech info."
    )

# --- TOOL 3: POLICY LOOKUP (Wrapper) ---
# This function takes the 'Brain' (qa_chain) and wraps it as a tool
def create_policy_tool(qa_chain):
    return Tool(
        name="lookup_internship_policy",
        func=qa_chain.run,
        description="Useful for reading the internal PDF guide to check policies."
    )

@tool
def get_todays_date(input_str: str = ""):
    """
    Returns the actual current date from the computer's internal clock.
    Always use this tool when you need to know 'today' or 'current date'.
    Ignore the input string.
    """
    # Returns format like: "February 02, 2026"
    return datetime.now().strftime("%B %d, %Y")