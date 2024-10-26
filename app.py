import subprocess
import os
import time
import io
from typing import Dict, List, Tuple, Optional
from PIL import Image
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, KeepTogether
from reportlab.lib.units import inch
from reportlab.lib.colors import Color
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ImageInfo:
    path: str
    page: int
    dimensions: Tuple[int, int]

class ContentExplainer:
    def __init__(self, temp_dir: str = "temp_images"):
        """Initialize the ContentExplainer with custom styles and temporary directory."""
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
        self.image_counter = 0
        self.temp_image_dir = Path(temp_dir)
        self.temp_image_dir.mkdir(exist_ok=True)

    def _create_custom_styles(self) -> Dict[str, ParagraphStyle]:
        """Create and return custom paragraph styles."""
        return {
            'Title': ParagraphStyle(
                'Title',
                parent=self.styles['Title'],
                fontSize=24,
                spaceAfter=30,
                alignment=1
            ),
            'Heading1': ParagraphStyle(
                'Heading1',
                parent=self.styles['Heading1'],
                fontSize=18,
                spaceAfter=20
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=self.styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                leading=16
            ),
            'Topic': ParagraphStyle(
                'Topic',
                parent=self.styles['Heading2'],
                fontSize=16,
                spaceAfter=15,
                textColor=Color(0.2, 0.2, 0.6)
            ),
            'ImageCaption': ParagraphStyle(
                'ImageCaption',
                parent=self.styles['Normal'],
                fontSize=10,
                alignment=1,
                textColor=Color(0.3, 0.3, 0.3)
            )
        }

    def detect_content_type(self, text: str) -> str:
        """Detect the type of content based on keyword frequency."""
        markers = {
            'technical': ['algorithm', 'implementation', 'system', 'process', 'technical', 'architecture'],
            'scientific': ['experiment', 'research', 'study', 'analysis', 'data', 'methodology'],
            'theoretical': ['theory', 'concept', 'principle', 'framework', 'model', 'approach'],
            'educational': ['learn', 'understand', 'explain', 'example', 'practice', 'exercise'],
            'business': ['strategy', 'market', 'business', 'management', 'organization', 'planning']
        }
        
        text = text.lower()
        scores = {category: sum(text.count(marker) for marker in markers[category])
                 for category in markers}
        
        return max(scores.items(), key=lambda x: x[1])[0]

    def generate_prompts(self, content_type: str) -> Dict[str, str]:
        """Generate appropriate prompts based on content type."""
        base_prompts = {
            'technical': {
                'beginner': "Please explain this technical content in simple terms for beginners: ",
                'intermediate': "Please provide a detailed technical explanation of: ",
                'advanced': "Please provide an in-depth technical analysis of: "
            },
            'scientific': {
                'beginner': "Please explain this scientific content in accessible terms: ",
                'intermediate': "Please provide a detailed scientific explanation of: ",
                'advanced': "Please provide an in-depth scientific analysis of: "
            },
            'theoretical': {
                'beginner': "Please explain these theoretical concepts in simple terms: ",
                'intermediate': "Please provide a detailed theoretical explanation of: ",
                'advanced': "Please provide an in-depth theoretical analysis of: "
            },
            'educational': {
                'beginner': "Please explain this educational material in student-friendly terms: ",
                'intermediate': "Please provide a comprehensive educational explanation of: ",
                'advanced': "Please provide an in-depth educational analysis of: "
            },
            'business': {
                'beginner': "Please explain this business content in simple terms: ",
                'intermediate': "Please provide a detailed business analysis of: ",
                'advanced': "Please provide an in-depth business analysis of: "
            }
        }
        
        return base_prompts.get(content_type, base_prompts['educational'])

    def extract_text_and_title_from_pdf(self, pdf_path: str) -> Tuple[str, str]:
        """Extract text and title from PDF file."""
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PdfReader(file)
                title = pdf_reader.metadata.get('/Title', '')
                
                if not title:
                    first_page_text = pdf_reader.pages[0].extract_text()
                    title = first_page_text.split('\n')[0].strip()
                
                text = [page.extract_text() or "" for page in pdf_reader.pages]
                return title, ' '.join(text)
                
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {e}")

    def call_llama_with_ollama(self, prompt: str, max_retries: int = 3) -> str:
        """Call the Llama model through Ollama with retry logic."""
        for attempt in range(max_retries):
            try:
                process = subprocess.Popen(
                    ["ollama", "run", "llama3.2", prompt],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                    
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=120)
                    if process.returncode == 0:
                        return stdout.strip()
                    print(f"Attempt {attempt + 1} failed with error: {stderr}")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"Attempt {attempt + 1} timed out")
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with exception: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(3)
                
        return "Failed to generate explanation after multiple attempts."

    def generate_explanations(self, note_text: str) -> Tuple[Dict[str, str], str]:
        """Generate explanations for different expertise levels."""
        content_type = self.detect_content_type(note_text)
        print(f"Detected content type: {content_type}")
        
        prompts = self.generate_prompts(content_type)
        max_chunk_size = 3000
        chunks = [note_text[i:i+max_chunk_size] for i in range(0, len(note_text), max_chunk_size)]
        
        explanations = {}
        for level, prompt_template in prompts.items():
            full_explanation = []
            for chunk in chunks:
                prompt = f"{prompt_template}\n\n{chunk}"
                chunk_explanation = self.call_llama_with_ollama(prompt)
                if chunk_explanation != "Failed to generate explanation after multiple attempts.":
                    full_explanation.append(chunk_explanation)
            
            explanations[level] = '\n\n'.join(full_explanation) if full_explanation else "No explanation generated."
        
        return explanations, content_type

    def create_level_pdf(self, content: str, title: str, level: str, content_type: str, 
                        output_filename: str) -> None:
        """Create a PDF document for a specific expertise level."""
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Add title and subtitle
        story.append(Paragraph(title, self.custom_styles['Title']))
        
        level_titles = {
            'beginner': 'Beginner-Friendly Guide',
            'intermediate': 'Comprehensive Guide',
            'advanced': 'Advanced Analysis'
        }
        level_subtitle = f"{level_titles[level]} - {content_type.title()} Content"
        story.append(Paragraph(level_subtitle, self.custom_styles['Heading1']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Process content sections
        sections = content.split('\n\n')
        
        for section in sections:
            if not section.strip():
                continue
                
            section = section.strip()
            if len(section) < 100 and any(char.isupper() for char in section):
                story.append(Paragraph(section, self.custom_styles['Topic']))
            else:
                story.append(Paragraph(section.replace('\n', ' '), self.custom_styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))

        doc.build(story)
        print(f"PDF created: {output_filename}")

    def cleanup(self) -> None:
        """Clean up temporary directory."""
        if self.temp_image_dir.exists():
            self.temp_image_dir.rmdir()

def main(pdf_path: str):
    """Main function to process a PDF file."""
    explainer = ContentExplainer()
    try:
        title, note_text = explainer.extract_text_and_title_from_pdf(pdf_path)
        explanations, content_type = explainer.generate_explanations(note_text)

        for level, content in explanations.items():
            output_filename = f"{level}_guide.pdf"
            explainer.create_level_pdf(content, title, level, content_type, output_filename)
    
    finally:
        explainer.cleanup()

if __name__ == "__main__":
    pdf_path = Path(r"C:\Users\ajogd\OneDrive\Desktop\New folder (3)\U2-OS - Process Scheduling Concepts.pdf")
    if pdf_path.exists():
        main(str(pdf_path))
    else:
        print("PDF file not found. Please check the path.")