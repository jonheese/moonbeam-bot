import json
import openai
from . import plugin

class AIPlugin(plugin.NoBotPlugin):
    def __make_ai_request(self, prompt):
        openai.api_key = self._config.get('PAWAN_KRD_API_KEY')
        openai.base_url = self._config.get('PAWAN_KRD_API_HOST')

        completion = openai.chat.completions.create(
            model="pai-001-light-beta",
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        return completion.choices[0].message.content

    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        if request['text'].lower().startswith("moonbeam ai"):
            prompt = ' '.join(request['text'].lower().split()[2:])
            if prompt:
                message_ts = self._web_client.chat_postMessage(
                    channel=request['channel'],
                    text=f'Hmmm, I\'ll have to think about for a second...',
                ).get('ts')
                self._log.debug(f"Got AI request: {request['text']}")
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': self.__make_ai_request(prompt=prompt),
                    }
                )
                if message_ts:
                    self._web_client.chat_delete(
                        channel=request['channel'],
                        ts=message_ts,
                    )
        return responses
