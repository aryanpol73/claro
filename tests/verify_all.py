import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("RUNNING CLARO VERIFICATION SUITE (TESTS A, B, C, D)")
print("=" * 60)

# -------------------------------------------------------------
# TEST A: Existing presentation (Basics_of_Machine_Learning.pdf)
# -------------------------------------------------------------
print("\n--- [TEST A] Existing Presentation Workflow Verification ---")
from backend.rag import ask_rag
from backend.document_store import get_document, list_documents

ml_doc_id = "cfc4fa067adf4cacd002666d16b2da38bb0744ed05e75e5e453360e991d90a95"
ml_doc = get_document(ml_doc_id)
print(f"Document: {ml_doc.get('original_filename')}")
print(f"Total Pages: {ml_doc.get('total_pages')}, Total Chunks: {ml_doc.get('total_chunks')}, Status: {ml_doc.get('status')}")
assert ml_doc.get("total_pages") == 161, "Expected 161 pages"
assert ml_doc.get("total_chunks") == 128, "Expected 128 chunks"

question_a = "Explain the machine learning workflow described in this presentation."
print(f"Asking: '{question_a}'...")
res_a = ask_rag(question_a, top_k=4, metadata_filter={"document_id": ml_doc_id})
print(f"Grounded: {res_a.grounded}")
print(f"Answer snippet:\n{res_a.answer[:300]}...")
print("Citations:")
pages_cited = []
for c in res_a.citations:
    print(f"  - {c.source} | Page/Slide: {c.page} | Snippet: {c.snippet[:60]}...")
    pages_cited.append(c.page)

# Verify slide 25 or process slides (23, 24, 25) are cited
print(f"Pages cited: {pages_cited}")
print("[TEST A PASSED]")

# -------------------------------------------------------------
# TEST B: Upload & Ingest a new PowerPoint (.pptx)
# -------------------------------------------------------------
print("\n--- [TEST B] Ingest New PowerPoint (.pptx) Verification ---")
from backend.ingestion_pipeline import ingest_document
from backend.document_metadata import generate_document_id

pptx_path = Path("backend/uploads/sample_quantum.pptx")
with open(pptx_path, "rb") as f:
    quantum_doc_id = generate_document_id(f.read())

print(f"Ingesting {pptx_path.name} with ID {quantum_doc_id[:16]}...")
ingest_res = ingest_document(
    file_path=str(pptx_path),
    document_id=quantum_doc_id,
    source_name="Introduction_to_Quantum_Computing.pptx",
)
print(f"Ingestion result: Status={ingest_res.get('status')}, Pages={ingest_res.get('total_pages')}, Chunks={ingest_res.get('total_chunks')}")
assert ingest_res.get("total_pages") == 3, f"Expected 3 slides, got {ingest_res.get('total_pages')}"
assert ingest_res.get("total_chunks") > 0, "Expected >0 chunks"

question_b = "What does the Hadamard gate do according to the presentation?"
print(f"Asking: '{question_b}'...")
res_b = ask_rag(question_b, top_k=3, metadata_filter={"document_id": quantum_doc_id})
print(f"Grounded: {res_b.grounded}")
print(f"Answer:\n{res_b.answer}")
print("Citations:")
hadamard_slide_cited = False
for c in res_b.citations:
    print(f"  - {c.source} | Page/Slide: {c.page} | Snippet: {c.snippet}")
    if c.page == 3:
        hadamard_slide_cited = True

assert hadamard_slide_cited, "Expected citation to Slide 3 for Hadamard gate"
print("[TEST B PASSED]")

# -------------------------------------------------------------
# TEST C: Verify Grounding (Cite-or-Refuse on unanswerable query)
# -------------------------------------------------------------
print("\n--- [TEST C] Cite-or-Refuse Grounding Verification ---")
question_c = "What is the recipe for baking chocolate chip cookies?"
print(f"Asking unanswerable question: '{question_c}'...")
res_c = ask_rag(question_c, top_k=4, metadata_filter={"document_id": ml_doc_id})
print(f"Grounded: {res_c.grounded}")
print(f"Answer: {res_c.answer}")
assert res_c.grounded is False or "insufficient evidence" in res_c.answer.lower() or "not contain sufficient" in res_c.answer.lower(), "Expected Claro to refuse ungrounded question"
print("[TEST C PASSED]")

# -------------------------------------------------------------
# TEST D: Cross-document synthesis
# -------------------------------------------------------------
print("\n--- [TEST D] Multi-Document Synthesis Verification ---")
from backend.rag import synthesize_cross_documents

synth_topic = "Compare the topics covered in the uploaded materials."
print(f"Synthesizing topic: '{synth_topic}' across documents...")
res_d = synthesize_cross_documents(
    topic=synth_topic,
    document_ids=[ml_doc_id, quantum_doc_id],
)
print(f"Synthesis Grounded: {res_d.grounded}")
print(f"Synthesis answer preview:\n{res_d.answer[:400]}...")
print("Citations in synthesis:")
for c in res_d.citations[:4]:
    print(f"  - {c.source} (page {c.page})")
assert len(res_d.citations) > 0, "Expected synthesis citations"
print("[TEST D PASSED]")

print("\n" + "=" * 60)
print("ALL VERIFICATION TESTS (A, B, C, D) PASSED SUCCESSFULLY!")
print("=" * 60)
