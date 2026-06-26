import sys
import pymoo

print(sys.version)
print(pymoo.__version__)


from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting



print("OK")
from pymoo.problems import get_problem

problem = get_problem("zdt1")
from pymoo.problems import get_problem
problem = get_problem("go-schaffer01")
print(problem)