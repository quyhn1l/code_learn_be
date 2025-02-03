# In các số nguyên tố từ 1 đến 20
for num in range(2, 21):
    if all(num % i != 0 for i in range(2, int(num**0.5) + 1)):
        print(num, "is a prime number")
