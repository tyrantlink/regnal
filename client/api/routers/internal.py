from .router import CrAPIRouter


class Internal(CrAPIRouter):
    async def get_bot_info(self, identifier: str) -> dict:
        request = await self.session.get(f'/i/bot/{identifier}')

        match request.status:
            case 200: pass
            case 403: raise ValueError('invalid crapi token!')
            case 503: raise ValueError('unable to reach the specified client!')
            case status: raise ValueError(f'unknown response code: {status}')

        return await request.json()

    async def reload_au(self) -> None:
        # ? this might have speed issues at scale
        request = await self.session.post('/i/reload_au')

        match request.status:
            case 200: pass
            case 403: raise ValueError('invalid crapi token!')
            case status:
                try:
                    json = await request.json()
                except Exception:
                    json = {}
                raise ValueError(
                    f'unknown response code: {status} | {json.get("detail","")}')
