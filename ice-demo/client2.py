import sys, Ice
import Demo
 
communicator = Ice.initialize(sys.argv)

host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
base1 = communicator.stringToProxy(f"SimplePrinter1:tcp -h {host} -p 5678")
base2 = communicator.stringToProxy(f"SimplePrinter2:tcp -h {host} -p 5678")
printer1 = Demo.PrinterPrx.checkedCast(base1)
printer2 = Demo.PrinterPrx.checkedCast(base2)
if (not printer1) or (not printer2):
    raise RuntimeError("Invalid proxy")

rep = printer1.printString("Hello World from printer1!")
print(rep)
rep = printer2.printString("Hello World from printer2!")
print(rep)

for printer in (printer1, printer2):
    print("Resultado da soma:", printer.soma(10, 20))
    print("Texto em maiusculas:", printer.maiuscula("sistemas distribuidos"))

communicator.destroy()
