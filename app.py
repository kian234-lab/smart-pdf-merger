import streamlit as st
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Professional PDF Binder",
    page_icon="📑",
    layout="centered"
)

# Hide Streamlit Branding (CSS Hack)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button {
        width: 100%;
        background-color: #0f172a;
        color: white;
        padding: 0.75rem;
        border-radius: 0.5rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1e293b;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---

def create_toc(file_names, page_counts):
    """Generates the Table of Contents Page"""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    width, height = letter

    # Header
    can.setFont("Helvetica-Bold", 18)
    can.drawString(50, height - 50, "Table of Contents")
    can.setLineWidth(1)
    can.line(50, height - 60, width - 50, height - 60)

    # Content
    y = height - 100
    can.setFont("Helvetica", 11)
    current_page = 2 # Starts after TOC

    for name, pages in zip(file_names, page_counts):
        # Truncate long names
        display_name = (name[:60] + '...') if len(name) > 60 else name

        # Dots for visual connection
        can.setFillColorRGB(0.5, 0.5, 0.5)
        can.drawString(50, y, display_name)
        can.drawRightString(width - 50, y, f"Page {current_page}")

        # Reset color
        can.setFillColorRGB(0, 0, 0)

        y -= 25
        current_page += pages

        if y < 50:
            can.showPage()
            y = height - 50

    can.save()
    packet.seek(0)
    return packet

def stamp_page_numbers(pdf_reader, start_page, total_pages):
    """Stamps 'Page X of Y' on every page"""
    writer = PdfWriter()
    for i, page in enumerate(pdf_reader.pages):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width, height = letter

        # Footer Style
        can.setFont("Helvetica", 9)
        can.setFillColorRGB(0.4, 0.4, 0.4)
        text = f"Page {start_page + i} of {total_pages}"
        can.drawCentredString(width / 2, 20, text)
        can.save()

        packet.seek(0)
        watermark = PdfReader(packet)
        page.merge_page(watermark.pages[0])
        writer.add_page(page)
    return writer

# --- 3. UI LAYOUT ---

st.title("📑 Pro Binder")
st.markdown("### The 'Table of Contents' Generator")
st.caption("Merge PDFs. Auto-generate Index. Auto-number Pages.")

uploaded_files = st.file_uploader(
    "Step 1: Upload PDFs (Drag to reorder list)",
    type="pdf",
    accept_multiple_files=True
)

# Settings
col1, col2 = st.columns(2)
with col1:
    use_toc = st.checkbox("Generate Table of Contents", value=True)
with col2:
    use_numbers = st.checkbox("Add Page Numbers", value=True)

# --- 4. EXECUTION LOGIC ---

if uploaded_files and st.button("Create Professional Bundle"):
    status = st.empty()
    status.info("⏳ Analyzing files...")

    try:
        # A. Analysis Phase
        readers = []
        file_names = []
        page_counts = []
        total_pages = 0

        for f in uploaded_files:
            reader = PdfReader(f)
            readers.append(reader)
            file_names.append(f.name)
            count = len(reader.pages)
            page_counts.append(count)
            total_pages += count

        if use_toc:
            total_pages += 1 # Add 1 for the TOC itself

        final_writer = PdfWriter()

        # B. TOC Phase
        if use_toc:
            status.info("⏳ Generating Table of Contents...")
            toc_packet = create_toc(file_names, page_counts)
            final_writer.add_page(PdfReader(toc_packet).pages[0])

        # C. Merging & Stamping Phase
        current_page_counter = 2 if use_toc else 1

        progress_bar = st.progress(0)

        for idx, (reader, count) in enumerate(zip(readers, page_counts)):
            status.info(f"⏳ Processing {file_names[idx]}...")

            if use_numbers:
                stamped_chunk = stamp_page_numbers(reader, current_page_counter, total_pages)
                for page in stamped_chunk.pages:
                    final_writer.add_page(page)
            else:
                for page in reader.pages:
                    final_writer.add_page(page)

            current_page_counter += count
            progress_bar.progress((idx + 1) / len(uploaded_files))

        # D. Finalize
        output = io.BytesIO()
        final_writer.write(output)
        status.success("✅ Done! Your bundle is ready.")

        st.download_button(
            label="Download Professional PDF",
            data=output.getvalue(),
            file_name="professional_bundle.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
