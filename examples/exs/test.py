import tellurium as te
r = te.loada('species z = 40 grams; z has mole;')
r.simulate(0, 50, 100)
r.plot()