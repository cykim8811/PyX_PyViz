
from XReact import createElement, host

class AdminComponent:
    def __render__(self, user):
        return createElement('div', {'className': 'admin-component'},
            createElement('p', {}, '관리자 컴포넌트입니다.')
        )

class UserComponent:
    def __render__(self, user):
        return createElement('div', {'className': 'user-component'},
            createElement('p', {}, '유저 컴포넌트입니다.')
        )

class Homepage:
    def __init__(self, title):
        self.title = title
        self.adminComponent = AdminComponent()
        self.userComponent = UserComponent()

    def __render__(self, user):
        if user.isAdmin:
            # 관리자 페이지 렌더링
            def setTitle(e):
                self.title = e['target']['value']
            return createElement('div', {'className': 'admin-page'},
                createElement('h1', {}, self.title),
                createElement('p', {}, '여기서 관리자는 시스템 설정을 변경할 수 있습니다.'),
                self.adminComponent,
                createElement('input', {
                    'type': 'text',
                    'value': self.title,
                    'onChange': setTitle
                    })
            )
        else:
            # 일반 사용자 페이지 렌더링
            def getRoot(e):
                user.isAdmin = True
            return createElement('div', {'className': 'user-page'},
                createElement('h1', {}, self.title),
                createElement('p', {}, '당신의 정보와 활동을 볼 수 있는 유저 페이지입니다.'),
                self.userComponent,
                createElement('input', {
                    'type': 'button',
                    'value': 'Get Root Privilege',
                    'onClick': getRoot
                    })
            )



host(Homepage('DefaultTitle'), port=7003)
