import os
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any
from docling.document_converter import DocumentConverter
from app.services.vector_db import vector_db

class KnowledgeBaseManager:
    def __init__(self, pdf_directory: str = "src", metadata_file: str = ".kb_metadata.json"):
        self.pdf_directory = Path(pdf_directory)
        self.metadata_file = Path(metadata_file)
        self.converter = DocumentConverter()
        
    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of a file."""
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _load_metadata(self) -> dict:
        """Load metadata about processed PDFs."""
        import json
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self, metadata: dict):
        """Save metadata about processed PDFs."""
        import json
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        
        lines = text.splitlines()

        def is_section_header(line: str) -> bool:
            return bool(re.match(r'^[A-Z]\.\s+\S.+$', line))

        def is_definition_header(line: str) -> bool:
            # Examples: "Mismatch. A mismatch occurs...", "Hardware. A hardware issue..."
            return bool(re.match(r'^[A-Z][A-Za-z0-9/\-\s]{1,40}\.\s+\S', line))

        paragraphs: List[str] = []
        buf: List[str] = []

        def flush():
            if not buf:
                return
            para = " ".join(buf).strip()
            para = re.sub(r"\s+", " ", para)
            if len(para) >= 50:
                paragraphs.append(para)
            buf.clear()

        for raw in lines:
            line = raw.strip()

            if not line:
                flush()
                continue

            # If a new header starts and we already have content, flush first
            if (is_section_header(line) or is_definition_header(line)) and buf:
                flush()

            buf.append(line)

        flush()
        return paragraphs

    
    def _extract_section_title(self, paragraph: str):
        """
        Extract section title if paragraph starts with one.
        Looks for patterns like "A. Title" or "Title." at the start.
        """
        # Pattern for section headers like "A. Issue Classification"
        section_match = re.match(r'^([A-Z]\.\s+[^\.]+)', paragraph)
        if section_match:
            return section_match.group(1).strip()
        
        # Pattern for bold/capitalized titles at start
        title_match = re.match(r'^([A-Z][^\.]{3,50}?)[\.\:]', paragraph)
        if title_match:
            return title_match.group(1).strip()
        
        return None
    
    def _merge_small_paragraphs(self, paragraphs: List[str], min_size: int = 200) -> List[str]:
        if not paragraphs:
            return []

        merged: List[str] = []
        carry = ""

        for p in paragraphs:
            if carry:
                p = carry + " " + p
                carry = ""

            # If the paragraph is tiny, hold it to merge with the next one
            if len(p) < min_size:
                if merged:
                    merged[-1] = merged[-1].rstrip() + "\n\n" + p
                else:
                    carry = p
            else:
                merged.append(p)

        if carry:
            # If file starts with a tiny fragment, keep it as is
            merged.append(carry)

        return merged

    
    def _clean_markdown(self, text: str) -> str:
        """
        Minimal cleanup: remove heading markers but keep content readable.
        Extend as needed (lists, links, etc.).
        """
        # Remove heading hashes at line start
        text = re.sub(r"(?m)^#{1,6}\s+", "", text)
        return text.strip()
    
    
    def process_pdf(self, pdf_path: Path, merge_small: bool = False) -> List[dict]:
        """Process a PDF and return paragraph-based chunks with metadata."""
        result = self.converter.convert(str(pdf_path))
        doc = result.document

        all_chunks: List[Dict[str, Any]] = []
        current_section = "Introduction"

        num_pages = doc.num_pages()
        for page_nr in range(1, num_pages + 1):
            page_doc = doc.filter(page_nrs={page_nr})
            page_md = page_doc.export_to_markdown()

            paragraphs = self._split_into_paragraphs(page_md)

            if merge_small:
                paragraphs = self._merge_small_paragraphs(paragraphs, min_size=200)

            for para_idx, paragraph in enumerate(paragraphs):
                section_title = self._extract_section_title(paragraph)
                if section_title:
                    current_section = section_title

                chunk_id = f"{pdf_path.stem}_p{page_nr}_para{para_idx}"

                all_chunks.append({
                    "text": self._clean_markdown(paragraph),
                    "metadata": {
                        "source": pdf_path.name,
                        "page": page_nr,
                        "paragraph_index": para_idx,
                        "section": current_section,
                        "chunk_id": chunk_id,
                        "char_count": len(paragraph),
                    }
                })

        return all_chunks

    
    def check_updates_needed(self) -> List[Path]:
        """Check which PDFs need to be processed."""
        metadata = self._load_metadata()
        files_to_process = []
        
        if not self.pdf_directory.exists():
            self.pdf_directory.mkdir(parents=True, exist_ok=True)
            return []
        
        for pdf_file in self.pdf_directory.glob("*.pdf"):
            current_hash = self._calculate_file_hash(pdf_file)
            stored_hash = metadata.get(str(pdf_file), {}).get("hash")
            
            if current_hash != stored_hash:
                files_to_process.append(pdf_file)
        
        return files_to_process
    
    def update_knowledge_base(self, vector_db):
        """Update vector database with new/modified PDFs."""
        files_to_process = self.check_updates_needed()
        
        if not files_to_process:
            print("✅ Knowledge base is up to date.")
            return 0
        
        print(f"📚 Processing {len(files_to_process)} PDF(s)...")
        metadata = self._load_metadata()
        total_chunks = 0
        
        for pdf_file in files_to_process:
            print(f"  📄 Processing: {pdf_file.name}")
            chunks = self.process_pdf(pdf_file, merge_small=False)
            print (chunks)
            
            # Add to vector database
            texts = [chunk["text"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            vector_db.add_documents(texts, metadatas)
            
            # Verify the addition
            count_after = vector_db.collection.count()
            print(f"    ✓ Extracted {len(chunks)} paragraphs")
            print(f"    📊 Collection now has {count_after} total documents")
            
            # Update metadata
            metadata[str(pdf_file)] = {
                "hash": self._calculate_file_hash(pdf_file),
                "chunks": len(chunks),
                "paragraphs_extracted": len(chunks),
                "last_processed": __import__('datetime').datetime.now().isoformat()
            }
            
            total_chunks += len(chunks)
            print(f"    ✓ Extracted {len(chunks)} paragraphs")
        
        self._save_metadata(metadata)
        print(f"✅ Successfully processed {total_chunks} paragraphs from {len(files_to_process)} file(s).")
        return total_chunks