# Home Design & Construction Management System

A Django-based management system that streamlines home design submissions, quote approvals, and construction progress tracking.

## Features
- User registration, login, and dashboard overview
- House design CRUD with image and file attachments
- Quote request workflow with admin approval and pricing
- Public house plan catalog with filters, galleries, and one-click quote conversion
- Construction project management with progress updates
- Email notifications (console backend) for key events
- Thai-language UI with contract PDF generation for quotes using WeasyPrint

## Tech Stack
- Python 3.12
- Django 5
- SQLite (development database)
- Bootstrap 5 for UI styling

## Getting Started
1. **Install dependencies**
   ```powershell
   C:\Project-House-phakphum\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
   > Pillow, Django, and WeasyPrint are required. WeasyPrint needs system GTK libraries on Windows—follow the official installation guide before generating PDFs.

2. **Apply migrations**
   ```powershell
   C:\Project-House-phakphum\.venv\Scripts\python.exe manage.py migrate
   ```

3. **Create a superuser**
   ```powershell
   C:\Project-House-phakphum\.venv\Scripts\python.exe manage.py createsuperuser
   ```

4. **Run development server**
   ```powershell
   C:\Project-House-phakphum\.venv\Scripts\python.exe manage.py runserver
   ```

5. **Access the app**
   - Application: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## Environment Notes
- Media uploads are stored in the `media/` directory.
- Emails are printed to the console via the console email backend.
- Bootstrap is loaded from a CDN; customize styling in `static/css/styles.css`.

## Testing
Run Django's test suite:
```powershell
C:\Project-House-phakphum\.venv\Scripts\python.exe manage.py test
```
