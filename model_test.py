from transformers import MarianMTModel, MarianTokenizer

model = MarianMTModel.from_pretrained("./fine_1")
tokenizer = MarianTokenizer.from_pretrained("./fine_1")

test_cumleleri = [
    "Watch out, enemy incoming!",
    "I need to save the game.",
    "You died. Restart?",
    "Pick up the weapon."
]

for cumle in test_cumleleri:
    inputs = tokenizer(cumle, return_tensors="pt")
    output = model.generate(**inputs)
    print(f"{cumle} → {tokenizer.decode(output[0], skip_special_tokens=True)}")