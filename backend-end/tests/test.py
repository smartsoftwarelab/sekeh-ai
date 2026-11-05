import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chat_api.service.qom_llm import qom_chat


if __name__ == "__main__":
    print(
        qom_chat(
            [{"role": "user", "content": "Hello World"}],
            temperature=0.7,
            max_tokens=1000,
        )
    )
