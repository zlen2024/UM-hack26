with open('backend/templates/dashboard.html', 'r') as f:
    content = f.read()

# Fix the empty for loop in the html template
content = content.replace('{% for opp in top_opportunities %}\n                                    \n                                    {% endfor %}', '')
content = content.replace('<tbody><tr', '{% for opp in top_opportunities %}\n<tbody><tr')
content = content.replace('</tr></tbody>', '</tr></tbody>\n{% endfor %}')

with open('backend/templates/dashboard.html', 'w') as f:
    f.write(content)
