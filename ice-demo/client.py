import sys, Ice
import Demo
 
communicator = Ice.initialize(sys.argv)

host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
base = communicator.stringToProxy(f"SimplePrinter:tcp -h {host} -p 5678")
printer = Demo.PrinterPrx.checkedCast(base)
if not printer:
    raise RuntimeError("Invalid proxy")

print("Resposta original:", printer.printString("Hello World!"))
print("Resultado da soma:", printer.soma(10, 20))
print("Texto em maiusculas:", printer.maiuscula("sistemas distribuidos"))
communicator.destroy()
