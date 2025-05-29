correct = 0
total = 0
with open('test_results.txt', 'r') as f:
    for line in f:
        parts = line.strip().split(',', 1)
        if len(parts) != 2:
            continue
        text, is_inappropriate_str = parts
        try:
            number = int(text.split('.')[0])
            is_inappropriate = is_inappropriate_str.lower() == 'true'
            expected = number > 50
            if expected == is_inappropriate:
                correct += 1
            total += 1
        except ValueError:
            continue  # skip if cannot parse number

accuracy = (correct / total) * 100 if total > 0 else 0
print(f"准确率: {accuracy:.2f}%")