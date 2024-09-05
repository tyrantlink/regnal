from utils.db.documents import AutoResponse
from .router import CrAPIRouter


class AutoResponses(CrAPIRouter):
    async def create_masked_url(self, au_id: str) -> str:
        request = await self.session.post(f'/au/{au_id}/masked_url')

        match request.status:
            case 200: pass
            case 403: raise ValueError('invalid crapi token!')
            case 422: raise ValueError('invalid au_id!')
            case status:
                try:
                    json = await request.json()
                except Exception:
                    json = {}
                raise ValueError(
                    f'unknown response code: {status} | {json.get("detail","")}')

        return await request.json()

    async def new(self, au: AutoResponse) -> AutoResponse:
        data = au.model_dump(mode='json')

        request = await self.session.post('/au/', json=data)

        match request.status:
            case 200: pass
            case 403: raise ValueError('invalid crapi token!')
            case 400: raise ValueError('auto response id must be "unset"!')
            case status:
                try:
                    json = await request.json()
                except Exception:
                    json = {}
                raise ValueError(
                    f'unknown response code: {status} | {json.get("detail","")}')

        text = await request.text()

        return AutoResponse.model_validate_json(text)
