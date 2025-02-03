# In dãy Fibonacci gồm 10 số đầu tiên
fib = [0, 1]
for i in range(8):
    fib.append(fib[-1] + fib[-2])
print(fib)
