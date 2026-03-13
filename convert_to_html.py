#!/usr/bin/env python3
"""
Convert THE_FEED_Volume_1_Expanded.md to HTML with Calibri font
"""
import re

def markdown_to_html(md_content):
    html_parts = []
    lines = md_content.split('\n')
    in_paragraph = False
    
    for line in lines:
        line = line.strip()
        
        if not line:
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
            continue
        
        # Headers
        if line.startswith('# '):
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
            title = line[2:].strip()
            html_parts.append(f'<h1>{title}</h1>')
        elif line.startswith('## '):
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
            title = line[3:].strip()
            html_parts.append(f'<h2>{title}</h2>')
        elif line.startswith('### '):
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
            title = line[4:].strip()
            html_parts.append(f'<h3>{title}</h3>')
        
        # Horizontal rules
        elif line == '---':
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
            html_parts.append('<div class="divider">* * *</div>')
        
        # Regular paragraphs
        else:
            # Convert markdown italics to HTML
            line = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', line)
            line = re.sub(r'_([^_]+)_', r'<em>\1</em>', line)
            
            if not in_paragraph:
                html_parts.append('<p>')
                in_paragraph = True
            else:
                html_parts.append(' ')
            
            html_parts.append(line)
    
    if in_paragraph:
        html_parts.append('</p>')
    
    return '\n'.join(html_parts)

def main():
    # Read the markdown file
    with open('/root/.openclaw/workspace/creative_projects/THE_FEED/01_GLITCH_PROTOCOL/The_Feed_Volume_1_Draft.md', 'r') as f:
        md_content = f.read()
    
    # Convert to HTML
    body_content = markdown_to_html(md_content)
    
    # Create full HTML document
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GLITCH PROTOCOL - Scott Smallbeck</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Calibri', 'Segoe UI', sans-serif;
            line-height: 1.8;
            color: #2c2c2c;
            background: #fafafa;
            font-size: 18px;
        }
        .container {
            max-width: 700px;
            margin: 0 auto;
            padding: 60px 40px;
            background: white;
            box-shadow: 0 0 40px rgba(0,0,0,0.05);
            min-height: 100vh;
        }
        header {
            text-align: center;
            padding: 60px 0 40px;
            border-bottom: 2px solid #1a1a2e;
            margin-bottom: 60px;
        }
        .series-title {
            font-size: 0.9em;
            letter-spacing: 4px;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 10px;
        }
        h1 {
            font-size: 2.8em;
            font-weight: normal;
            color: #1a1a2e;
            margin-bottom: 15px;
            font-style: italic;
        }
        .subtitle {
            font-size: 1.1em;
            color: #888;
            font-style: italic;
        }
        h2 {
            font-size: 1.5em;
            font-weight: normal;
            color: #1a1a2e;
            margin: 50px 0 30px;
            text-align: center;
            font-style: italic;
        }
        h3 {
            font-size: 1.2em;
            font-weight: normal;
            color: #444;
            margin: 40px 0 20px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        p {
            margin-bottom: 1.5em;
            text-align: justify;
            text-indent: 2em;
        }
        p:first-of-type {
            text-indent: 0;
        }
        .chapter-break {
            text-align: center;
            margin: 60px 0;
            color: #999;
            font-size: 1.5em;
            letter-spacing: 10px;
        }
        em {
            font-style: italic;
        }
        .dialogue {
            margin-left: 2em;
        }
        .divider {
            text-align: center;
            margin: 40px 0;
            color: #ccc;
            letter-spacing: 20px;
        }
        .title-page {
            text-align: center;
            margin: 100px 0;
        }
        .copyright-page {
            font-size: 0.9em;
            color: #666;
            margin: 60px 0;
        }
        @media (max-width: 600px) {
            .container {
                padding: 40px 25px;
            }
            h1 {
                font-size: 2em;
            }
            body {
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        {body}
    </div>
</body>
</html>'''
    
    full_html = html_template.replace('{body}', body_content)
    
    # Write output - replace the existing Draft.html
    output_path = '/root/.openclaw/workspace/creative_projects/THE_FEED/01_GLITCH_PROTOCOL/The_Feed_Volume_1_Draft.html'
    with open(output_path, 'w') as f:
        f.write(full_html)
    
    print(f"Converted to HTML: {output_path}")

if __name__ == '__main__':
    main()
