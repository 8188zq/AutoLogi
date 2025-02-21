from openai import OpenAI
import copy
import traceback
import time
import os

def call_openai(**kwargs):
    payload = copy.deepcopy(kwargs)
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
    )
    assert 'model' in payload
    max_try = 3
    for i in range(max_try):
        try:
            completion = client.chat.completions.create(
                **payload
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(traceback.format_exc())
            time.sleep(10)
    raise Exception('Max Retry...')

if __name__ == '__main__':
    pass
    