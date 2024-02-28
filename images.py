import requests
import fitz
from PIL import Image
import os
import json

local_doc_path = "local.pdf"
document_url = "https://utfs.io/f/bd660644-8819-4562-8fd0-f67753da0509-ke7kh8.pdf"

# Download the PDF file locally if it doesn't exist
if not os.path.exists(local_doc_path):
    with open(local_doc_path, "wb") as f:
        pdf_file_content = requests.get(document_url).content
        f.write(pdf_file_content)

# Run Reducto's API on the file
if os.path.exists("reducto_output.json"):
    output = json.load(open("reducto_output.json"))
else:
    response = requests.post("https://api.reducto.ai/chunk_url", headers={
        "accept": "application/json",
        "authorization": f"Bearer {os.environ['REDUCTO_API_TOKEN']}"
    },params={
        "document_url": document_url
    })
    output = response.json()
    with open("reducto_output.json", "w") as f:
        json.dump(output, f)

# Grab all of the figure blocks
with fitz.open(local_doc_path) as doc:
    for chunk in output:
        for block_type, bbox in zip(chunk["metadata"]["types"], chunk["metadata"]["bbox"]):
            print(block_type)
            print(bbox)
            if block_type == "Figure":
                doc.load_page(bbox["page"] - 1)
                page = doc.load_page(bbox["page"] - 1)
                rect = fitz.Rect(bbox["left"] * page.rect.width,
                                 bbox["top"] * page.rect.height,
                                 (bbox["left"] + bbox["width"]) * page.rect.width,
                                 (bbox["top"] + bbox["height"]) * page.rect.height)
                pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=rect)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.save(f"figure_page_{bbox['page']}.png")