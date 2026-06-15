import os
import zipfile

def create_project_zip():
    # Define source directory and target destination path
    source_dir = os.path.dirname(os.path.abspath(__file__))
    desktop_dir = os.path.dirname(source_dir)  # 'Hotel management' is on Desktop, so parent is Desktop
    
    zip_filename = "hotel_booking_project.zip"
    zip_filepath = os.path.join(desktop_dir, zip_filename)
    
    # Folders and files to exclude from the zip archive
    exclude_folders = {'.git', 'venv', '__pycache__', '.gemini'}
    exclude_extensions = {'.pyc', '.pyo', '.zip'}
    
    print(f"Archiving project from: {source_dir}")
    print(f"Target archive path:   {zip_filepath}\n")
    
    files_added = 0
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Exclude folders in-place so os.walk doesn't recurse into them
            dirs[:] = [d for d in dirs if d not in exclude_folders]
            
            for file in files:
                # Get file extension and verify it's not excluded
                _, ext = os.path.splitext(file)
                if ext.lower() in exclude_extensions or file == zip_filename:
                    continue
                
                # Full path to write
                full_path = os.path.join(root, file)
                
                # Relative path inside the zip file
                rel_path = os.path.relpath(full_path, source_dir)
                
                zipf.write(full_path, rel_path)
                print(f" [+] Added: {rel_path}")
                files_added += 1
                
    print(f"\nSuccessfully archived {files_added} files into '{zip_filepath}'.")

if __name__ == "__main__":
    create_project_zip()
