from au_scripts.auto_responses.lib.models import Message as AUMessage, Channel as AUChannel, Guild as AUGuild, User as AUUser
from utils.db.documents.ext.enums import AutoResponseMethod, AutoResponseType
from asyncio import create_task, get_event_loop, wait_for, TimeoutError
from au_scripts.auto_responses import SCRIPTED_AUTO_RESPONSES
from regex import search, fullmatch, escape, IGNORECASE
from argparse import ArgumentParser, ArgumentError
from concurrent.futures import ThreadPoolExecutor
from utils.db import AutoResponse
from discord import Message
from typing import TypeVar
from random import random
from client import Client

A = TypeVar('A')


class ArgParser(ArgumentParser):
    def __init__(self, message: str) -> None:
        super().__init__(exit_on_error=False, add_help=False)
        self.add_argument('--delete', '-d', action='store_true')
        self.add_argument('--seed', '-s', type=int)
        self.add_argument('--au', '-a', type=str)
        self.add_argument('--force', '-f', action='store_true')
        self.add_argument('--reply', '-r', action='store_true')
        self.delete: bool = False
        self.seed: int | None = None
        self.au: str | None = None
        self.force: bool = False
        self.reply: bool = False
        self.message: str = message

        try:
            self.parse(message)
        except ArgumentError:
            pass

    def __bool__(self) -> bool:
        return (
            self.delete is True or
            self.seed is not None or
            self.au is not None or
            self.force is True
        )

    def parse(self, message: str) -> None:
        args, message = self.parse_known_args(message.split(' '))

        self.message = ' '.join(message)
        self.delete = args.delete
        self.seed = args.seed
        self.au = args.au
        self.force = args.force
        self.reply = args.reply


class AutoResponseCarrier:
    def __init__(self, au: list[AutoResponse]) -> None:
        self.all = set(au)
        self.base = set(filter(lambda a: a.id.startswith('b'), self.all))
        self._custom = set(filter(lambda a: a.id.startswith('c'), self.all))
        self._unique = set(filter(lambda a: a.id.startswith('u'), self.all))
        self._mention = set(filter(lambda a: a.id.startswith('m'), self.all))
        self._personal = set(filter(lambda a: a.id.startswith('p'), self.all))
        self._scripted = set(filter(lambda a: a.id.startswith('s'), self.all))

    def custom(self, guild_id: int) -> list[AutoResponse]:
        return set(filter(lambda au: au.data.guild == guild_id, self._custom))

    def unique(self, guild_id: int) -> list[AutoResponse]:
        return set(filter(lambda au: au.data.guild == guild_id, self._unique))

    def mention(self, user_id: int = None, user_ids: list[int] = None) -> list[AutoResponse]:
        if user_id and user_ids:
            raise ValueError('cannot specify both user_id and user_ids')

        if user_id:
            return set(filter(lambda au: au.trigger == str(user_id), self._mention))

        if user_ids:
            return set(filter(lambda au: au.trigger in [str(a) for a in user_ids], self._mention))

        return self._mention

    def personal(self, user_id: int) -> list[AutoResponse]:
        return set(filter(lambda au: au.data.user == user_id, self._personal))

    def scripted(self, guild_imported: set[str]) -> list[AutoResponse]:
        return set(filter(lambda au: au.id in guild_imported, self._scripted))


class AutoResponses:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client
        self.au: AutoResponseCarrier = AutoResponseCarrier([])

    def __iter__(self) -> iter:
        return iter(self.au)

    def __len__(self) -> int:
        return len(self.au)

    async def reload_au(self, use_cache: bool = True) -> None:
        self.au = AutoResponseCarrier(
            await AutoResponse.find(ignore_cache=not use_cache).to_list()
        )
        SCRIPTED_AUTO_RESPONSES.cache.clear()

    async def delete(self, au_id: str) -> None:
        au = self.get(au_id)

        if au is None:
            raise ValueError(f'auto response {au_id} not found')

        au.type = AutoResponseType.deleted

        await au.save_changes()

        new_all = self.au.all
        new_all.discard(au)
        new_all.add(au)

        self.au = AutoResponseCarrier(new_all)

    def find(self, attrs: dict = None, limit: int = None) -> list[AutoResponse]:
        if attrs is None:
            return self.au

        out = set()

        for au in self.au.all:
            if all(getattr(au, k) == v for k, v in attrs.items()):
                out.add(au)
                if limit is not None and len(out) >= limit:
                    break

        return list(out)

    def get(self, _id: str) -> AutoResponse | None:
        if res := self.find({'id': _id}, 1):
            return res[0]
        return None

    def get_with_overrides(self, _id: str, overrides: dict) -> AutoResponse | None:
        if res := self.find({'id': _id}, 1):
            return res[0].with_overrides(overrides)
        return None

    def match(self, message: str, overrides: dict | None = None, pool: set[AutoResponse] | None = None) -> set[AutoResponse]:
        if overrides is None:
            overrides = {}

        if pool is None:
            pool = self.au.all

        found = []

        for au in pool:
            au = au.with_overrides(
                overrides[au.id]) if au.id in overrides else au

            trigger = au.trigger if au.data.regex else escape(au.trigger)

            match au.method:
                case AutoResponseMethod.exact:
                    match = fullmatch(
                        rf'{trigger}(\.|\?|\!)*',
                        message,
                        0 if au.data.case_sensitive else IGNORECASE
                    )
                case AutoResponseMethod.contains:
                    match = search(
                        rf'(^|\s){trigger}(\.|\?|\!)*(\s|$)',
                        message,
                        0 if au.data.case_sensitive else IGNORECASE
                    )
                case AutoResponseMethod.regex:
                    match = search(
                        au.trigger,
                        message,
                        0 if au.data.case_sensitive else IGNORECASE
                    )
                case AutoResponseMethod.mention:
                    match = search(
                        rf'<@!?{au.trigger}>(\s|$)',
                        message,
                        0 if au.data.case_sensitive else IGNORECASE
                    )
                case AutoResponseMethod.disabled:
                    continue
                case _:
                    raise ValueError(
                        f'invalid auto response method: {au.method}')

            if match is not None:
                found.append(au)

        return found

    def random_choice(self, pool: list[tuple[A, int | None]]) -> A:
        choices, weights = zip(*pool)
        rand = random()*sum(weights)

        cum = 0  # please, it stands for cumulative
        for choice, weight in zip(choices, weights):
            cum += weight

            if rand <= cum:
                return choice

        raise ValueError(
            f'random choice failed with {rand=}, {cum=}, {sum(weights)=}'
        )

    def insert_regex_groups(self, response: AutoResponse, message: str) -> str:
        if response.data.regex and (match := search(response.trigger, message, IGNORECASE)):
            groups = {f'g{i}': '' for i in range(1, 11)}

            groups.update(
                {
                    f'g{k}': v
                    for k, v in
                    enumerate(
                        match.groups()[:10], 1
                    )
                    if v is not None
                }
            )
            try:
                formatted_response = response.response.format(**groups)
            except KeyError:
                return None

            if formatted_response == response.response:
                return None

            return formatted_response

    async def get_response(
        self,
        message: Message,
        args: ArgParser,
        overrides: dict[str, dict],
        cross_guild: bool = False,
        custom_only: bool = False
    ) -> AutoResponse | None:
        if self.client is None:
            raise ValueError(
                'AutoResponses object must have client set to get response'
            )

        if message.guild is None:
            raise ValueError('message must be from a guild!')

        # check if --au can be used, return if so
        _user = await self.client.db.user(message.author.id)
        user_found = _user.data.auto_responses.found if _user else []

        if args.au is not None:
            response = self.get_with_overrides(
                args.au, overrides.get(args.au, {}))

            if (
                    response is not None and
                    (
                        args.force or not
                        (
                            response.id not in user_found or
                            response.data.guild not in [message.guild.id, None] and
                            not cross_guild or
                            response.method == AutoResponseMethod.disabled or
                            response.type == AutoResponseType.deleted
                        )
                    )
            ):
                if search(r'\{g\d+\}', response.response):
                    formatted_response = self.insert_regex_groups(
                        response, args.message
                    )

                    if formatted_response is None:
                        create_task(
                            self.client.helpers.notify_reaction(
                                message, delay=2)
                        )
                        return None

                    response = response.with_overrides(
                        {'response': formatted_response}
                    )

                return response

            create_task(self.client.helpers.notify_reaction(message))

        imported_scripts = set(
            (await self.client.db.guild(message.guild.id)
             ).data.auto_responses.imported_scripts
        )
        # gather matches
        if custom_only:
            matches = [
                *self.match(
                    args.message,
                    overrides,
                    self.au.custom(message.guild.id)
                )
            ]
        else:
            matches = [
                # personal responses
                *self.match(
                    args.message,
                    overrides,
                    self.au.personal(message.author.id)
                ),
                # mention responses
                *self.match(
                    args.message,
                    overrides,
                    self.au.mention(
                        user_ids=[
                            a.id
                            for a in
                            message.mentions
                            if f'<@{a.id}>' in
                            args.message
                        ]
                    )
                ),
                # custom responses
                *self.match(
                    args.message,
                    overrides,
                    self.au.custom(message.guild.id)
                ),
                # unique responses
                *self.match(
                    args.message, overrides,
                    self.au.unique(message.guild.id)
                ),
                # scripted responses
                *self.match(
                    args.message,
                    overrides,
                    self.au.scripted(imported_scripts)
                ),
                # base responses
                *self.match(args.message, overrides, self.au.base)
            ]
        # strip user disabled
        matches = [
            a
            for a in matches
            if a.id
            not in _user.data.auto_responses.disabled
        ]
        # strip nsfw if channel is not nsfw
        if not message.channel.is_nsfw():
            matches = [a for a in matches if not a.data.nsfw]

        if not matches:
            return None

        if args.seed is not None:
            if not (args.seed >= len(matches)):
                response = matches[args.seed]

                if args.force or response.id in user_found:
                    return response

            create_task(self.client.helpers.notify_reaction(message, delay=2))

        # strip user restricted
        matches = [
            a
            for a in matches
            if a.data.user
            in {None, message.author.id}
        ]
        # choose a match
        options = [(a, a.data.weight) for a in matches]

        while options:
            choice = self.random_choice(options)

            if args.force or choice.data.chance >= random()*100:
                response = choice
                break

            options.remove((choice, choice.data.weight))
        else:
            return None
        # insert regex groups
        if search(r'\{g\d+\}', response.response):
            formatted_response = self.insert_regex_groups(
                response, args.message
            )

            if formatted_response is None:
                create_task(
                    self.client.helpers.notify_reaction(message, delay=2)
                )
                return None

            response = response.with_overrides(
                {'response': formatted_response}
            )

        return response

    async def execute_au(
        self,
        au: AutoResponse,
        message: Message,
        args: ArgParser
    ) -> str | tuple[str, list[AutoResponse.AutoResponseData.AutoResponseFollowup]] | None:
        script = SCRIPTED_AUTO_RESPONSES.get(au.response)

        if script is None:
            return None

        au_message = AUMessage(
            id=message.id,
            author=AUUser(
                name=message.author.name,
                id=message.author.id,
                created_at=message.author.created_at,
                nickname=message.author.nick),
            channel=AUChannel(
                name=message.channel.name,
                id=message.channel.id,
                nsfw=message.channel.is_nsfw()),
            guild=AUGuild(
                name=message.guild.name,
                id=message.guild.id,
                me=AUUser(
                    name=message.guild.me.name,
                    id=message.guild.me.id,
                    created_at=message.guild.me.created_at,
                    nickname=message.guild.me.nick)),
            content=args.message
        )

        with ThreadPoolExecutor() as executor:
            future = get_event_loop().run_in_executor(
                executor,
                script,
                au_message
            )

            try:
                script_response = await wait_for(future, timeout=5)
            except TimeoutError:
                executor.shutdown(wait=False, cancel_futures=True)
                return None

        if isinstance(script_response, str):
            return script_response

        response, followups = script_response
        followups = [
            AutoResponse.AutoResponseData.AutoResponseFollowup(
                delay=d,
                response=r)
            for d, r in followups
        ]

        return response, followups
