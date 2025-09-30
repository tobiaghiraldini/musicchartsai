from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.static import serve
import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def docs_view(request):
    """Serve the MkDocs generated documentation."""
    try:
        # Path to the generated MkDocs site
        docs_site_path = os.path.join(settings.BASE_DIR, 'site')
        
        # Check if the site exists, if not build it
        if not os.path.exists(docs_site_path):
            build_docs()
        
        # Serve the index.html file
        index_path = os.path.join(docs_site_path, 'index.html')
        
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace relative paths with absolute paths for static assets
            content = content.replace('href="assets/', f'href="/docs/assets/')
            content = content.replace('src="assets/', f'src="/docs/assets/')
            content = content.replace('href="css/', f'href="/docs/css/')
            content = content.replace('src="js/', f'src="/docs/js/')
            
            return HttpResponse(content, content_type='text/html')
        else:
            return HttpResponse("Documentation is being built. Please try again in a moment.", status=503)
            
    except Exception as e:
        logger.error(f"Error serving documentation: {e}")
        return HttpResponse("Error loading documentation. Please contact support.", status=500)

def docs_static(request, path):
    """Serve static files and HTML pages from the MkDocs site."""
    docs_site_path = os.path.join(settings.BASE_DIR, 'site')
    
    # Handle .md file requests by converting to HTML
    if path.endswith('.md'):
        # Convert .md to directory/index.html
        path = path[:-3] + '/index.html'
    
    # Handle directory requests by adding index.html
    if not path.endswith('.html') and not path.endswith('/'):
        # Check if it's a directory that should have an index.html
        potential_dir = os.path.join(docs_site_path, path)
        if os.path.isdir(potential_dir):
            path = os.path.join(path, 'index.html').replace('\\', '/')
    
    # Handle directory requests ending with slash
    if path.endswith('/'):
        path = path + 'index.html'
    
    file_path = os.path.join(docs_site_path, path)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        if file_path.endswith('.html'):
            # Serve HTML files with proper content type and path fixes
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix relative paths in HTML content
            content = content.replace('href="assets/', f'href="/docs/assets/')
            content = content.replace('src="assets/', f'src="/docs/assets/')
            content = content.replace('href="css/', f'href="/docs/css/')
            content = content.replace('src="js/', f'src="/docs/js/')
            
            return HttpResponse(content, content_type='text/html')
        else:
            # Serve other static files normally
            return serve(request, path, document_root=docs_site_path)
    else:
        raise Http404(f"File not found: {path}")

def build_docs():
    """Build the MkDocs documentation site."""
    try:
        # Change to project directory
        project_dir = settings.BASE_DIR
        
        # Run mkdocs build command
        result = subprocess.run(
            ['mkdocs', 'build'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"MkDocs build failed: {result.stderr}")
            raise Exception(f"MkDocs build failed: {result.stderr}")
        
        logger.info("MkDocs documentation built successfully")
        
    except subprocess.TimeoutExpired:
        logger.error("MkDocs build timed out")
        raise Exception("Documentation build timed out")
    except Exception as e:
        logger.error(f"Error building documentation: {e}")
        raise

def rebuild_docs(request):
    """Rebuild the documentation (admin only)."""
    if not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)
    
    try:
        build_docs()
        return HttpResponse("Documentation rebuilt successfully", status=200)
    except Exception as e:
        return HttpResponse(f"Error rebuilding documentation: {e}", status=500)
