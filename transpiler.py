import re

def transform_nested_pyx_with_newlines_and_variables_corrected(pyx_code):
    # 태그 이름, 속성, 자식을 추출하는 정규 표현식 (줄바꿈 포함)
    tag_pattern = r"<(\w+)([^>]*)>([\s\S]*?)</\1>"
    
    # 속성을 파싱하는 함수
    def parse_attributes(attrs_str):
        attrs = {}
        attr_pattern = r"(\w+)=\"([^\"]*)\""
        for attr, value in re.findall(attr_pattern, attrs_str):
            attrs[attr] = value
        return attrs

    # 중첩된 PYX 및 줄바꿈 처리를 위한 함수
    def transform(match):
        tag, attrs_str, children_str = match.groups()
        attrs = parse_attributes(attrs_str)

        # 줄바꿈을 제거하고 중첩된 태그를 재귀적으로 변환
        children_str = re.sub(tag_pattern, transform, children_str.replace("\n", " ").strip())

        # 자식 요소를 문자열과 변수로 구분
        children = []
        for child in children_str.split(","):
            child = child.strip()
            if child:
                # 문자열이 아닌 경우 변수로 처리
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', child):
                    children.append(child)
                else:
                    children.append(f"'{child}'")
        return f"create_py_element('{tag}', {attrs}, {', '.join(children)})"

    # PYX 코드에서 패턴을 찾아 변환
    return re.sub(tag_pattern, transform, pyx_code)


with open("main.py", "r", encoding="utf-8") as f:
    pyx_code = f.read()

# 변환된 JavaScript 코드
py_code = transform_nested_pyx_with_newlines_and_variables_corrected(pyx_code)

with open("main.x.py", "w", encoding="utf-8") as f:
    f.write(py_code)