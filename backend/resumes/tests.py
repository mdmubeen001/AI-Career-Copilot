import io
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

import docx
from pypdf import PdfWriter

from .models import Resume, ResumeAnalysis
from .services.document_parser import DocumentParser
from .services.resume_analyzer import ResumeAnalyzer

User = get_user_model()


def create_mock_docx(text="Sample Resume Content with Python and React."):
    doc = docx.Document()
    doc.add_paragraph(text)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def create_mock_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return buffer.getvalue()


class ResumeModuleTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='resume_user1@example.com',
            password='TestPassword123!',
            username='resume_user1'
        )
        self.user2 = User.objects.create_user(
            email='resume_user2@example.com',
            password='TestPassword123!',
            username='resume_user2'
        )

        self.upload_url = reverse('resume-upload')
        self.list_url = reverse('resume-list')

    def test_unauthenticated_access_denied(self):
        """Verify endpoints require authentication."""
        resp1 = self.client.get(self.list_url)
        self.assertEqual(resp1.status_code, status.HTTP_401_UNAUTHORIZED)

        resp2 = self.client.post(self.upload_url, {})
        self.assertEqual(resp2.status_code, status.HTTP_401_UNAUTHORIZED)

        detail_url = reverse('resume-detail', kwargs={'pk': 999})
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_401_UNAUTHORIZED)

        analyze_url = reverse('resume-analyze', kwargs={'pk': 999})
        self.assertEqual(self.client.post(analyze_url, {}).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_invalid_file_extension(self):
        """Uploading non-pdf/non-docx files must return 400 Bad Request."""
        self.client.force_authenticate(user=self.user1)

        invalid_file = SimpleUploadedFile(
            "resume.txt",
            b"This is a plain text file.",
            content_type="text/plain"
        )
        response = self.client.post(self.upload_url, {'file': invalid_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)

    def test_upload_file_too_large(self):
        """Uploading files exceeding MAX_UPLOAD_SIZE must return 400 Bad Request."""
        self.client.force_authenticate(user=self.user1)

        large_bytes = b"x" * (6 * 1024 * 1024)  # 6 MB
        oversized_file = SimpleUploadedFile(
            "huge_resume.pdf",
            large_bytes,
            content_type="application/pdf"
        )
        response = self.client.post(self.upload_url, {'file': oversized_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_and_parse_valid_docx(self):
        """Uploading a valid DOCX extracts text and persists Resume model."""
        self.client.force_authenticate(user=self.user1)

        docx_content = create_mock_docx(
            "Jane Doe\nSoftware Engineer\nExperience: Built Python Django microservices and React web apps."
        )
        valid_file = SimpleUploadedFile(
            "Jane_Doe_Resume.docx",
            docx_content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        response = self.client.post(
            self.upload_url,
            {'file': valid_file, 'auto_analyze': 'false'},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['original_filename'], 'Jane_Doe_Resume.docx')
        self.assertEqual(response.data['file_type'], 'docx')
        self.assertIn('Python', response.data['extracted_text'])
        self.assertIn('React', response.data['extracted_text'])

    def test_user_isolation_for_resumes(self):
        """Users can only view and analyze their own resumes."""
        resume = Resume.objects.create(
            user=self.user1,
            original_filename="user1_resume.pdf",
            extracted_text="Python Engineer with 5 years experience.",
            file_type="pdf",
            file_size=1024
        )

        # Authenticate as user2
        self.client.force_authenticate(user=self.user2)

        # Listing resumes returns 0 for user2
        list_resp = self.client.get(self.list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data), 0)

        # Detail endpoint returns 404 for user2
        detail_url = reverse('resume-detail', kwargs={'pk': resume.id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_404_NOT_FOUND)

        # Analyze endpoint returns 404 for user2
        analyze_url = reverse('resume-analyze', kwargs={'pk': resume.id})
        analyze_resp = self.client.post(analyze_url, {'target_role': 'Python Developer'})
        self.assertEqual(analyze_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_resume_analysis_heuristic_engine(self):
        """Executing analysis on a resume returns a structured AI ATS assessment."""
        self.client.force_authenticate(user=self.user1)

        sample_text = """
        John Developer
        Email: john@example.com | Phone: 123-456-7890
        Summary: Versatile Senior Full Stack Software Engineer with 6+ years of experience.
        Skills: Python, Django, FastAPI, React, TypeScript, PostgreSQL, Docker, AWS, Git.
        Experience:
        Senior Software Engineer at Tech Corp (2021 - Present)
        - Developed REST APIs and microservices using Python, Django, and PostgreSQL.
        - Led cloud migration to AWS with Docker containerization, reducing latency by 35%.
        Education:
        B.S. in Computer Science, State University, 2019.
        Projects:
        - Built automated CI/CD pipeline and open source monitoring tool.
        """
        resume = Resume.objects.create(
            user=self.user1,
            original_filename="John_Developer_Resume.pdf",
            extracted_text=sample_text,
            file_type="pdf",
            file_size=2048
        )

        analyze_url = reverse('resume-analyze', kwargs={'pk': resume.id})
        response = self.client.post(
            analyze_url,
            {'target_role': 'Senior Backend Engineer'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data

        self.assertIn('ats_score_estimate', data)
        self.assertGreaterEqual(data['ats_score_estimate'], 50)
        self.assertLessEqual(data['ats_score_estimate'], 100)

        # Check detected skills
        detected_lower = [s.lower() for s in data['detected_skills']]
        self.assertIn('python', detected_lower)
        self.assertIn('django', detected_lower)
        self.assertIn('docker', detected_lower)

        # Check sections
        self.assertTrue(len(data['strengths']) > 0)
        self.assertTrue(len(data['recommendations']) > 0)
        self.assertIn('State University', data['education_summary'])

    def test_delete_resume(self):
        """User can delete their own uploaded resume."""
        self.client.force_authenticate(user=self.user1)

        resume = Resume.objects.create(
            user=self.user1,
            original_filename="to_delete.pdf",
            extracted_text="Some text",
            file_type="pdf",
            file_size=512
        )

        detail_url = reverse('resume-detail', kwargs={'pk': resume.id})
        del_resp = self.client.delete(detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Resume.objects.filter(id=resume.id).exists())
