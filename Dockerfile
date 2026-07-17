FROM python:3.11-slim
 
WORKDIR /app
 
# LibreOffice (headless) powers the faithful DOCX->PDF conversion.
# Font substitutes make the render match common resume fonts:
#   fonts-liberation      -> Arial / Times New Roman / Courier metric-compatible
#   fonts-crosextra-carlito -> Calibri
#   fonts-crosextra-caladea -> Cambria
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    fonts-liberation \
    fonts-crosextra-carlito \
    fonts-crosextra-caladea \
    && rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY . .
 
CMD streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
 
