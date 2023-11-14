
from XReact import createElement, host

class Homepage:
    def __init__(self, title):
        self.title = title
        self.adminComponent = AdminComponent()
        self.userComponent = UserComponent()

    def __render__(self, user):
        if hasattr(user, 'isAdmin') and user.isAdmin:
            # 관리자 페이지 렌더링
            def setTitle(e):
                self.title = e['target']['value']
            return (
                <div className='admin-page'>
                    <h1>{self.title}</h1>
                    <p>여기서 관리자는 시스템 설정을 변경할 수 있습니다.</p>
                    {self.adminComponent}
                    <input type='text' value={self.title} onChange={setTitle} />
                </div>
            )
        else:
            # 일반 사용자 페이지 렌더링
            return (
                <div className='user-page'>
                    <h1>{self.title}</h1>
                    <p>당신의 정보와 활동을 볼 수 있는 유저 페이지입니다.</p>
                    {self.userComponent}
                </div>
            )


host(Homepage('DefaultTitle'), port=7003)
