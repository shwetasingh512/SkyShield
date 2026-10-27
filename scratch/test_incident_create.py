import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skyshield.settings')
django.setup()
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
User = get_user_model()
# find a reporter user
user = User.objects.filter(groups__name='Reporter').first()
if not user:
    user = User.objects.filter(is_staff=False).first()
if not user:
    print('No reporter user found')
    sys.exit(1)
client = Client()
client.force_login(user)
post_data = {
    'title': 'Test Incident',
    'incident_type': 'RUNWAY_INCURSION',
    'occurrence_date': '2023-01-01T12:00',
    'location': 'KJFK',
    'description': 'Test description',
    'initial_severity': '3',
    'initial_likelihood': '2',
}
file_data = SimpleUploadedFile('test.txt', b'hello world', content_type='text/plain')
# combine data for multipart
response = client.post('/incidents/report/', data={**post_data, 'file': file_data, 'description': 'test file'}, follow=True)
print('Status code:', response.status_code)
print('Redirect chain:', response.redirect_chain)
print('Content length:', len(response.content))
