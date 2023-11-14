import re

tag_start = re.compile(r'<([a-z]+) ([^>]+)>')   # ex) <div className='admin-page'>
tag_end = re.compile(r'</([a-z]+)>')            # ex) </html>
tag_self_closing = re.compile(r'<([a-z]+)/>')   # ex) <br/>
tag_attr_single = re.compile(r"([a-zA-Z]+)='([^']+)'")
tag_attr_double = re.compile(r'([a-zA-Z]+)="([^"]+)"')
tag_code = re.compile(r'{([^}]+)}')             # ex) {self.title}



with open('main.x.py', 'r') as f:
    pyx_code = f.read()

pyx_code = "<div className='admin-page' onClick={setTitle} style='color: red;'>"

tag_stack = []

while True:
    tag_start_match = tag_start.search(pyx_code)
    if tag_start_match:
        tag_name = tag_start_match.group(1)
        tag_stack.append(tag_name)
        tag_start_attrs = tag_start_match.group(2)
        print(f'Found tag_start: {tag_name} with attrs: {tag_start_attrs}')

        attrs = {}
        tag_attr_single_match = tag_attr_single.findall(tag_start_attrs)
        tag_attr_double_match = tag_attr_double.findall(tag_start_attrs)
        tag_code_match = tag_code.findall(tag_start_attrs)
        if len(tag_attr_single_match):
            for tag_attr_name, tag_attr_value in tag_attr_single_match:
                print(f'Found tag_attr_single: {tag_attr_name} with value: {tag_attr_value}')
                attrs[tag_attr_name] = f"'{tag_attr_value}'"
        if len(tag_attr_double_match):
            for tag_attr_name, tag_attr_value in tag_attr_double_match:
                print(f'Found tag_attr_double: {tag_attr_name} with value: {tag_attr_value}')
                attrs[tag_attr_name] = f'"{tag_attr_value}"'
        if len(tag_code_match):
            for tag_code_value in tag_code_match:
                print(f'Found tag_code: {tag_code_value}')
                attrs[tag_code_value] = tag_code_value

        tag_stack.append({
            'tag': tag_name,
            'attrs': attrs,
            'children': []
        })
