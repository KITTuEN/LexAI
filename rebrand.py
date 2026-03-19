import os

def rebrand_files():
    files = [
        'templates/ocr.html', 'templates/member_home.html', 
        'templates/generator.html', 'templates/base.html', 
        'services/translations.py', 'services/rag_service.py', 
        'services/email_service.py', 'routes/chat.py', 
        'PROJECT_OVERVIEW.TXT', 'PRESENTATION.TXT', 
        'models/case.py', 'details.txt', 'abstract.txt'
    ]
    
    replacements = {
        'LexAI': 'NyayaVyavasth',
        'Lex Ai': 'NyayaVyavasth',
        'Lex AI': 'NyayaVyavasth'
    }
    
    for filename in files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in replacements.items():
                    new_content = new_content.replace(old, new)
                
                if new_content != content:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated: {filename}")
                else:
                    print(f"No changes needed: {filename}")
            except Exception as e:
                print(f"Error updating {filename}: {e}")
        else:
            print(f"File not found: {filename}")

if __name__ == '__main__':
    rebrand_files()
