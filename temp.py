import jedi

s = jedi.Script('''
a = 5
b = ''')
breakpoint()
result = s.complete()
print(result)
