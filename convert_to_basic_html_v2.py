#!/usr/bin/env python3
"""
Convert The_Feed_Volume_1_Draft.md to basic HTML with <br> tags 
Special handling for Companion dialogue with mixed quotes and asterisks
"""
import re

def markdown_to_basic_html(md_content):
    html_parts = []
    lines = md_content.split('\n')
    
    for line in lines:
        original_line = line
        line = line.rstrip()
        
        # Skip editorial comments
        if line.strip().startswith('[End of') or 'more lines in file' in line:
            continue
            
        # Skip empty lines (but add <br> for spacing)
        if not line.strip():
            html_parts.append('<br>')
            continue
        
        # Headers - convert to bold
        if line.startswith('# '):
            title = line[2:].strip()
            if title == 'GLITCH PROTOCOL':
                html_parts.append(f'<b><i>{title}</i></b><br>')
            else:
                html_parts.append(f'<b>{title}</b><br>')
        
        elif line.startswith('## '):
            title = line[3:].strip()
            if title == 'THE FEED Book 1':
                html_parts.append(f'<i>{title}</i><br>')
            else:
                html_parts.append(f'<b>{title}</b><br>')
        
        elif line.startswith('### '):
            title = line[4:].strip()
            html_parts.append(f'<b>{title}</b><br>')
        
        # Horizontal rules
        elif line.strip() == '---':
            html_parts.append('<br>***<br>')
        
        # Bold text (**text**)
        elif line.startswith('**') and line.endswith('**') and '**' not in line[2:-2]:
            text = line[2:-2]
            html_parts.append(f'<b>{text}</b><br>')
        
        # Regular paragraphs - handle Companion dialogue
        else:
            # Pattern 1: *Maya,* or *text* (italicize the whole thing)
            # Pattern 2: "Maya,* (starts with quote, ends with asterisk)
            # Pattern 3: "text* (starts with quote, ends with asterisk)
            # Pattern 4: *text" (starts with asterisk, ends with quote)
            
            # First, handle the mixed quote-asterisk patterns for Companion dialogue
            # "Maya,* -> "<i>Maya,</i>
            # "text* -> "<i>text</i>
            # *text" -> <i>text</i>"
            
            # Handle: "word,* or "words,* (quote at start, asterisk after comma/words)
            line = re.sub(r'"([^"]+),\*', r'"<i>\1,</i>', line)
            line = re.sub(r'"([^"]+)\*', r'"<i>\1</i>', line)
            
            # Handle: *word" or *words" (asterisk at start, quote at end)
            line = re.sub(r'\*([^"]+)"', r'<i>\1</i>"', line)
            
            # Handle standalone asterisk-wrapped text *text*
            line = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', line)
            
            # Also handle _text_ italics
            line = re.sub(r'_(.+?)_', r'<i>\1</i>', line)
            
            html_parts.append(f'{line}<br>')
    
    return '\n'.join(html_parts)

def main():
    # Read the markdown file
    with open('/root/.openclaw/workspace/creative_projects/THE_FEED/01_GLITCH_PROTOCOL/The_Feed_Volume_1_Draft.md', 'r') as f:
        md_content = f.read()
    
    # Convert to HTML
    body_content = markdown_to_basic_html(md_content)
    
    # Create basic HTML document
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GLITCH PROTOCOL - Scott Smallbeck</title>
</head>
<body>
{body}
</body>
</html>'''
    
    full_html = html_template.replace('{body}', body_content)
    
    # Write output
    output_path = '/root/.openclaw/workspace/creative_projects/THE_FEED/01_GLITCH_PROTOCOL/The_Feed_Volume_1_Draft_basic.html'
    with open(output_path, 'w') as f:
        f.write(full_html)
    
    print(f"Converted to basic HTML: {output_path}")

if __name__ == '__main__':
    main()
