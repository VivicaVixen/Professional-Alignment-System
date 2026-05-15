"""Smoke test del shim. Requiere llama-swap arrancado en 8080."""
import pas_inference_client as ic


def test_chat_qwen_basic():
    r = ic.chat(
        model="qwen2.5-coder:7b",
        messages=[{"role": "user", "content": "Say only the word: pong"}],
        options={"num_predict": 10, "temperature": 0.0},
    )
    assert r["done"] is True
    assert "message" in r and "content" in r["message"]
    assert len(r["message"]["content"]) > 0


def test_chat_deepseek_basic():
    r = ic.chat(
        model="deepseek-r1:7b",
        messages=[{"role": "user", "content": "Reply with the single word OK."}],
        options={"num_predict": 20, "temperature": 0.0},
    )
    assert r["done"] is True
    assert len(r["message"]["content"]) > 0


if __name__ == "__main__":
    test_chat_qwen_basic()
    print("qwen OK")
    test_chat_deepseek_basic()
    print("deepseek OK")
